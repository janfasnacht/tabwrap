from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pathlib import Path
import tempfile
import os
from werkzeug.utils import secure_filename
from click.testing import CliRunner
from .cli import main
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='tabwrap_')
os.chmod(UPLOAD_FOLDER, 0o755)
ALLOWED_EXTENSIONS = {'tex'}


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_compilation_options(request_form: dict) -> dict:
    """Parse and set up compilation options from request form data."""
    return {
        'output': UPLOAD_FOLDER,
        'suffix': '_compiled',
        'packages': request_form.get('packages', ''),
        'landscape': request_form.get('landscape', 'false').lower() == 'true',
        'no_rescale': request_form.get('no_rescale', 'false').lower() == 'true',
        'show_filename': request_form.get('show_filename', 'false').lower() == 'true',
        'keep_tex': False,
        'png': request_form.get('png', 'false').lower() == 'true',
        'combine_pdf': False
    }


def build_cli_args(input_path: Path, options: dict) -> list:
    """Build command line arguments for the TeX compiler."""
    args = ['--input', str(input_path), '--output', options['output']]

    # Optional arguments
    if options['suffix']: args.extend(['--suffix', options['suffix']])
    if options['packages']: args.extend(['--packages', options['packages']])
    if options['landscape']: args.append('--landscape')
    if options['no_rescale']: args.append('--no-rescale')
    if options['show_filename']: args.append('--show-filename')
    if options['keep_tex']: args.append('--keep-tex')
    if options['png']: args.append('--png')

    return args


def cleanup_files(input_path: Path):
    """Clean up temporary files after compilation."""
    cleanup_files = [
        input_path,
        *Path(UPLOAD_FOLDER).glob(f"{input_path.stem}*")
    ]
    for file in cleanup_files:
        try:
            os.remove(file)
        except (FileNotFoundError, PermissionError):
            logger.warning(f"Failed to remove temporary file: {file}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/api/compile', methods=['POST'])
def compile_tex():
    """Endpoint to compile TeX tables."""
    if not os.access(UPLOAD_FOLDER, os.W_OK):
        return jsonify({'error': 'Upload folder is not writable'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Save and process file
        filename = secure_filename(file.filename)
        input_path = Path(UPLOAD_FOLDER) / filename
        file.save(input_path)

        # Set up compilation
        options = setup_compilation_options(request.form)
        args = build_cli_args(input_path, options)

        # Run compilation
        runner = CliRunner()
        result = runner.invoke(main, args)

        if result.exit_code != 0:
            logger.error(f"Compilation failed: {result.output}")
            return jsonify({'error': f'Compilation failed: {result.output}'}), 500

        # Prepare output
        output_extension = '.png' if options['png'] else '.pdf'
        output_filename = input_path.stem + options['suffix'] + output_extension
        output_path = Path(options['output']) / output_filename

        if not output_path.exists():
            return jsonify({'error': 'Output file not found'}), 500

        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        logger.exception("Error during compilation")
        return jsonify({'error': str(e)}), 500

    finally:
        cleanup_files(input_path)


if __name__ == '__main__':
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    app.run(debug=True, port=5001)