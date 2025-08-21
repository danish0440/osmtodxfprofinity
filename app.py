#!/usr/bin/env python3
"""
OSM to DXF Converter Web Application
Flask-based web interface for converting OpenStreetMap data to AutoCAD DXF format.

Author: OSM to DXF Converter
Version: 1.0.0
"""

import os
import uuid
import threading
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Flask, request, jsonify, render_template, send_file, abort
from flask_cors import CORS

# Import our converter
from osm_to_dxf import OSMHandler, DXFGenerator

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['SECRET_KEY'] = 'osm-to-dxf-converter-secret-key'

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Global storage for conversion jobs
conversion_jobs = {}

class ConversionJob:
    """Represents a conversion job with status tracking."""
    
    def __init__(self, job_id, filename, projection='EPSG:3857', plan_type='key-plan'):
        self.job_id = job_id
        self.filename = filename
        self.projection = projection
        self.plan_type = plan_type
        # Configure settings based on plan type
        if plan_type == 'key-plan':
            self.use_colors = False  # Monochrome for professional look
            self.include_footpaths = False  # Simplified
            self.include_minor_roads = True
            self.include_buildings = True
            self.building_style = 'outline'
        else:  # location-plan
            self.use_colors = True   # Colored for detailed analysis
            self.include_footpaths = True   # Full detail
            self.include_minor_roads = True
            self.include_buildings = True
            self.building_style = 'filled'
        self.status = 'pending'  # pending, processing, completed, error
        self.progress = 0
        self.message = 'Job created'
        self.created_at = datetime.now()
        self.completed_at = None
        self.error_message = None
        self.output_file = None
        self.stats = {}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'osm', 'xml'}

def convert_osm_to_dxf(job_id):
    """Background task to convert OSM to DXF."""
    job = conversion_jobs[job_id]
    
    try:
        job.status = 'processing'
        job.message = 'Starting conversion...'
        job.progress = 10
        
        # Input and output paths
        input_path = Path(app.config['UPLOAD_FOLDER']) / job.filename
        output_filename = f"{Path(job.filename).stem}_{job_id}.dxf"
        output_path = Path(app.config['OUTPUT_FOLDER']) / output_filename
        
        job.message = 'Parsing OSM data...'
        job.progress = 20
        
        # Parse OSM data
        handler = OSMHandler()
        handler.apply_file(str(input_path))
        
        job.message = f'Parsed {len(handler.nodes)} nodes, {len(handler.ways)} ways, {len(handler.relations)} relations'
        job.progress = 50
        job.stats = {
            'nodes': len(handler.nodes),
            'ways': len(handler.ways),
            'relations': len(handler.relations)
        }
        
        # Generate DXF
        job.message = 'Generating DXF...'
        job.progress = 70
        
        dxf_gen = DXFGenerator(job.projection, job.use_colors)
        
        # Process data
        job.message = 'Processing nodes...'
        dxf_gen.process_nodes(handler.nodes)
        
        job.message = 'Processing ways...'
        job.progress = 85
        dxf_gen.process_ways(handler.ways, handler.nodes)
        
        # Save DXF file
        job.message = 'Saving DXF file...'
        job.progress = 95
        dxf_gen.save(str(output_path))
        
        # Complete job
        job.status = 'completed'
        job.message = 'Conversion completed successfully!'
        job.progress = 100
        job.completed_at = datetime.now()
        job.output_file = output_filename
        job.stats['layers'] = len(dxf_gen.created_layers)
        job.stats['file_size'] = output_path.stat().st_size
        
    except Exception as e:
        job.status = 'error'
        job.message = f'Conversion failed: {str(e)}'
        job.error_message = str(e)
        job.progress = 0

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start conversion."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .osm or .xml files'}), 400
    
    # Get options from form data
    projection = request.form.get('projection', 'EPSG:3857')
    plan_type = request.form.get('plan_type', 'key-plan')
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filename = f"{job_id}_{filename}"
    file_path = Path(app.config['UPLOAD_FOLDER']) / filename
    file.save(str(file_path))
    
    # Create conversion job
    job = ConversionJob(job_id, filename, projection, plan_type)
    conversion_jobs[job_id] = job
    
    # Start conversion in background
    thread = threading.Thread(target=convert_osm_to_dxf, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'File uploaded successfully. Conversion started.',
        'status': 'pending'
    })

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get conversion job status."""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    
    response = {
        'job_id': job_id,
        'status': job.status,
        'progress': job.progress,
        'message': job.message,
        'created_at': job.created_at.isoformat(),
        'stats': job.stats
    }
    
    if job.completed_at:
        response['completed_at'] = job.completed_at.isoformat()
        response['duration'] = (job.completed_at - job.created_at).total_seconds()
    
    if job.error_message:
        response['error'] = job.error_message
    
    if job.output_file:
        response['download_url'] = f'/api/download/{job_id}'
    
    return jsonify(response)

@app.route('/api/download/<job_id>')
def download_file(job_id):
    """Download converted DXF file."""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    
    if job.status != 'completed' or not job.output_file:
        return jsonify({'error': 'File not ready for download'}), 400
    
    file_path = Path(app.config['OUTPUT_FOLDER']) / job.output_file
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=f"{Path(job.filename).stem}.dxf",
        mimetype='application/octet-stream'
    )

@app.route('/api/jobs')
def list_jobs():
    """List all conversion jobs."""
    jobs_list = []
    
    for job_id, job in conversion_jobs.items():
        job_info = {
            'job_id': job_id,
            'filename': job.filename,
            'status': job.status,
            'progress': job.progress,
            'message': job.message,
            'created_at': job.created_at.isoformat(),
            'projection': job.projection
        }
        
        if job.completed_at:
            job_info['completed_at'] = job.completed_at.isoformat()
            job_info['duration'] = (job.completed_at - job.created_at).total_seconds()
        
        if job.output_file:
            job_info['download_url'] = f'/api/download/{job_id}'
        
        jobs_list.append(job_info)
    
    # Sort by creation time (newest first)
    jobs_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({'jobs': jobs_list})

@app.route('/api/projections')
def get_projections():
    """Get list of supported coordinate projections."""
    projections = [
        {'code': 'EPSG:3857', 'name': 'Web Mercator (Google Maps)', 'description': 'Most common web mapping projection'},
        {'code': 'EPSG:4326', 'name': 'WGS84 Geographic', 'description': 'Standard GPS coordinates'},
        {'code': 'EPSG:32633', 'name': 'UTM Zone 33N', 'description': 'Universal Transverse Mercator'},
        {'code': 'EPSG:32634', 'name': 'UTM Zone 34N', 'description': 'Universal Transverse Mercator'},
        {'code': 'EPSG:32635', 'name': 'UTM Zone 35N', 'description': 'Universal Transverse Mercator'},
        {'code': 'EPSG:3395', 'name': 'World Mercator', 'description': 'World Mercator projection'},
        {'code': 'EPSG:2154', 'name': 'RGF93 / Lambert-93', 'description': 'France national projection'},
        {'code': 'EPSG:25832', 'name': 'ETRS89 / UTM zone 32N', 'description': 'European projection'},
    ]
    
    return jsonify({'projections': projections})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🌐 OSM to DXF Converter Web Application")
    print("📍 Starting server at http://localhost:5000")
    print("📁 Upload folder:", Path(app.config['UPLOAD_FOLDER']).absolute())
    print("📁 Output folder:", Path(app.config['OUTPUT_FOLDER']).absolute())
    
    app.run(debug=True, host='0.0.0.0', port=5000)
