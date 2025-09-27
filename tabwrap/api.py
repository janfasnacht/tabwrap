# tabwrap/api.py
try:
    from flask import Flask, request, send_file
    from flask_restx import Api, Resource, fields, reqparse
    from flask_cors import CORS
    from werkzeug.utils import secure_filename
    from werkzeug.datastructures import FileStorage
except ImportError as e:
    raise ImportError(
        "API dependencies not installed. Install with: pip install tabwrap[api]"
    ) from e

from pathlib import Path
from datetime import datetime
import os
import tempfile

from .core import TexCompiler, CompilerMode
from .latex import FileValidationError, is_valid_tabular_content
from .config import setup_logging

logger = setup_logging(
    module_name=__name__,
    log_file=Path("logs") / f"api_{datetime.now():%Y%m%d}.log"
)

def create_app(config=None):
    """Create Flask app with API."""
    app = Flask(__name__)
    CORS(app)
    
    if config:
        app.config.update(config)
    
    # Configure API
    api = Api(
        app,
        version='1.0',
        title='TabWrap API',
        description='LaTeX table fragment compilation API',
        doc='/api/docs/',
        prefix='/api'
    )
    
    # Define API models
    compile_model = api.model('CompileOptions', {
        'packages': fields.String(description='Comma-separated LaTeX packages', example='booktabs,siunitx'),
        'landscape': fields.Boolean(description='Use landscape orientation', default=False),
        'no_rescale': fields.Boolean(description='Disable automatic table resizing', default=False),
        'show_filename': fields.Boolean(description='Show filename as header', default=False),
        'png': fields.Boolean(description='Output PNG instead of PDF', default=False),
        'svg': fields.Boolean(description='Output SVG instead of PDF', default=False),
        'combine_pdf': fields.Boolean(description='Combine multiple PDFs (not applicable for single files)', default=False),
    })
    
    def parse_bool(value):
        """Parse boolean from string, handling 'false' correctly."""
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    # File upload parser
    upload_parser = reqparse.RequestParser()
    upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='LaTeX table file')
    upload_parser.add_argument('packages', type=str, help='Comma-separated LaTeX packages', default='')
    upload_parser.add_argument('landscape', type=parse_bool, help='Use landscape orientation', default=False)
    upload_parser.add_argument('no_rescale', type=parse_bool, help='Disable automatic table resizing', default=False)
    upload_parser.add_argument('show_filename', type=parse_bool, help='Show filename as header', default=False)
    upload_parser.add_argument('png', type=parse_bool, help='Output PNG instead of PDF', default=False)
    upload_parser.add_argument('svg', type=parse_bool, help='Output SVG instead of PDF', default=False)
    
    @api.route('/health')
    class HealthCheck(Resource):
        def get(self):
            """Health check endpoint"""
            return {'status': 'healthy', 'version': '1.0.0'}
    
    @api.route('/compile')
    class CompileTable(Resource):
        @api.expect(upload_parser)
        @api.doc('compile_table')
        @api.response(200, 'Success - returns compiled file')
        @api.response(400, 'Bad Request - invalid input')
        @api.response(500, 'Internal Server Error - compilation failed')
        def post(self):
            """Compile LaTeX table fragment to PDF, PNG, or SVG"""
            try:
                args = upload_parser.parse_args()
                file = args['file']
                
                if not file or not allowed_file(file.filename):
                    api.abort(400, 'Invalid file. Only .tex files are allowed.')
                
                # Validate mutually exclusive options
                if args['png'] and args['svg']:
                    api.abort(400, 'Cannot specify both PNG and SVG output formats.')
                
                # Create temporary directory
                temp_dir = Path(tempfile.mkdtemp())
                
                try:
                    # Save uploaded file
                    filename = secure_filename(file.filename)
                    input_path = temp_dir / filename
                    file.save(str(input_path))
                    
                    # Validate content
                    with open(input_path, 'r') as f:
                        content = f.read()
                    
                    if not is_valid_tabular_content(content):
                        api.abort(400, 'Invalid LaTeX content. Must contain tabular environment.')
                    
                    # Compile
                    with TexCompiler(mode=CompilerMode.WEB) as compiler:
                        try:
                            output_path = compiler.compile_tex(
                                input_path=input_path,
                                output_dir=temp_dir,
                                packages=args['packages'],
                                landscape=args['landscape'],
                                no_rescale=args['no_rescale'],
                                show_filename=args['show_filename'],
                                png=args['png'],
                                svg=args['svg'],
                                keep_tex=False
                            )
                        except FileValidationError as e:
                            api.abort(400, f'Invalid file content: {str(e)}')
                        except RuntimeError as e:
                            # Check if it's a validation error
                            if 'Invalid tabular content' in str(e) or 'No tabular environment found' in str(e):
                                api.abort(400, f'Invalid LaTeX content: {str(e)}')
                            else:
                                api.abort(500, f'Compilation failed: {str(e)}')
                    
                    # Determine content type
                    if args['svg']:
                        mimetype = 'image/svg+xml'
                        ext = 'svg'
                    elif args['png']:
                        mimetype = 'image/png'
                        ext = 'png'
                    else:
                        mimetype = 'application/pdf'
                        ext = 'pdf'
                    
                    return send_file(
                        output_path,
                        mimetype=mimetype,
                        as_attachment=True,
                        download_name=f"{Path(filename).stem}_compiled.{ext}"
                    )
                    
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    api.abort(500, f'Server error: {str(e)}')
                finally:
                    # Cleanup handled by TexCompiler context manager
                    pass
                    
            except Exception as e:
                logger.error(f"API error: {e}")
                api.abort(500, f'Server error: {str(e)}')
    
    return app

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'tex'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# For backwards compatibility
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)