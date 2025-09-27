# tabwrap/api.py
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from .core import TexCompiler, CompilerMode
from .utils.validation import FileValidationError, is_valid_tabular_content
from .utils.logging import setup_logging
logger = setup_logging(
    module_name=__name__,
    log_file=Path("logs") / f"api_{datetime.now():%Y%m%d}.log"
)

SWAGGER_URL = "/api/docs"  # Swagger UI endpoint
API_URL = "/docs/openapi.yaml"  # Link to OpenAPI schema

app = Flask(__name__)
CORS(app)
swagger_ui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

ALLOWED_EXTENSIONS = {'tex'}


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_options(form_data: dict) -> dict:
    """Parse compilation options from form data."""
    return {
        'suffix': '_compiled',
        'packages': form_data.get('packages', ''),
        'landscape': form_data.get('landscape', 'false').lower() == 'true',
        'no_rescale': form_data.get('no_rescale', 'false').lower() == 'true',
        'show_filename': form_data.get('show_filename', 'false').lower() == 'true',
        'keep_tex': False,  # Always false in web mode
        'png': form_data.get('png', 'false').lower() == 'true',
        'combine_pdf': form_data.get('combine_pdf', 'false').lower() == 'true',
        'recursive': False  # Not applicable for web API single file uploads
    }


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/api/compile', methods=['POST'])
def compile_tex():
    """
    Compile TeX table endpoint.

    Expects:
        - multipart/form-data with a 'file' field containing the .tex file
        - optional compilation parameters in form fields

    Returns:
        - Compiled PDF/PNG file for download
        - JSON error response if compilation fails
    """
    logger.info("Received compilation request")

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    input_path = None
    content = ""

    try:
        # Create compiler instance in web mode
        with TexCompiler(mode=CompilerMode.WEB) as compiler:
            # Get temporary directory from compiler
            if not compiler.temp_dir:
                return jsonify({'error': 'Failed to create temporary directory'}), 500

            # Option A: File upload
            if 'file' in request.files:
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No selected file'}), 400
                if not allowed_file(file.filename):
                    return jsonify({'error': 'Invalid file type'}), 400

                filename = secure_filename(file.filename)
                input_path = compiler.temp_dir / filename
                file.save(input_path)
                logger.debug(f"File received: {filename}")
                logger.info(f"Saved file to: {input_path}")

                with open(input_path, 'r') as f:
                    content = f.read()

            # Option B: Raw pasted text
            elif 'text' in request.form:
                text = request.form['text']
                if not text.strip():
                    return jsonify({'error': 'Empty text input'}), 400
                filename = "pasted_input.tex"
                input_path = compiler.temp_dir / filename
                with open(input_path, 'w') as f:
                    f.write(text)
                content = text
                logger.info(f"Saved pasted text to: {input_path}")

            else:
                return jsonify({'error': 'No input provided (file or text)'}), 400

            # Validate content
            is_valid, error = is_valid_tabular_content(content)
            if not is_valid:
                return jsonify({'error': f'Invalid table content: {error}'}), 400

            # Parse options and compile
            options = parse_options(request.form)
            logger.info(f"Starting compilation with options: {options}")
            output_path = compiler.compile_tex(
                input_path=input_path,
                output_dir=compiler.temp_dir,
                **options
            )

            # Determine output file
            suffix = options['suffix']
            output_extension = '.png' if options['png'] else '.pdf'
            expected_output = compiler.temp_dir / f"{input_path.stem}{suffix}{output_extension}"

            if not expected_output.exists():
                logger.error(f"Output file not found: {expected_output}")
                return jsonify({'error': 'Output file not found'}), 500

            return send_file(
                output_path,
                as_attachment=True,
                download_name=expected_output.name,
                mimetype='application/pdf' if output_extension == '.pdf' else 'image/png'
            )

    except FileValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception("Error during compilation")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size too large error."""
    return jsonify({'error': 'File too large'}), 413


@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error'}), 500


def create_app(test_config=None):
    """Create and configure the Flask app."""
    if test_config:
        app.config.update(test_config)

    # Configure maximum file size (e.g., 16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    return app


@app.route('/docs/openapi.yaml')
def serve_openapi():
    """Serve OpenAPI schema"""
    docs_dir = os.path.join(os.path.dirname(__file__), "docs")
    return send_from_directory(docs_dir, "openapi.yaml")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
