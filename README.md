# document-flow

A Django-based web application for converting files between various formats with document access control features.

![main_page.png](readme-images/main_page.png)

## Table of Contents
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [License](#license)
- [Support](#support)

## Features

### File Conversion Capabilities
1. **HTML to PDF Conversion**
   - Convert HTML files or web pages to PDF documents
   - Supports custom styling and page configuration

![html-to-pdf.png](readme-images/html-to-pdf.png)

2. **Microsoft Word to PDF**
   - Convert DOC/DOCX files to PDF format
   - Preserves formatting and document structure

3. **Image Processing**
   - Multiple images to single PDF conversion (JPG, PNG)
   - Image to grayscale conversion
   - BMP to JPG conversion with quality adjustment

4. **PDF to Word**
   - Extract content from PDF to editable Word document
   - Basic formatting preservation

### Document Management
- **User Dashboard**
  - View uploaded original files
  - Access converted files
  - Manage shared documents

![profile.png](readme-images/profile.png)

- **Access Control**
  - Grant/revoke access to specific documents
  - Set permission levels (view/download)
  - Track document access history

![give-access.png](readme-images/give-access.png)

### API Services
- User management endpoints:
  - User registration
  - User profile management
  - Account deletion
- HTML to PDF conversion endpoint
- Document access control API

![api.png](readme-images/api.png)

## Technologies

### Core Stack
- Python 3.x
- Django 5.x
- Django REST Framework (for API endpoints)

### Conversion Tools
- **PDF Generation**: pdfkit/wkhtmltopdf (for HTML to PDF)
- **Word Processing**: python-docx (for Word operations)
- **Image Processing**: Pillow (for image manipulation)
- **PDF Parsing**: pdf2docx (for PDF to Word)

### Database
- PostgreSQL (recommended for production)
- SQLite (default for development)
