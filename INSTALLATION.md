# DocTura Desktop - Installation Guide

## Prerequisites

- Python 3.10 or higher
- Git (for cloning the repository)
- Tesseract OCR (optional, for OCR functionality)

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bofe82frank/DOCTURA.git
cd DOCTURA
```

### 2. Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

**For development (includes testing tools):**
```bash
pip install -e ".[dev]"
```

**With AI support (optional):**
```bash
pip install -e ".[ai]"
```

## Optional: Install Tesseract OCR

### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR`
3. Add to PATH or set `TESSERACT_CMD` environment variable

### macOS
```bash
brew install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
```

## Running the Application

### GUI Application

```bash
python -m docutura.app.main
```

Or if installed as a package:

```bash
docutura
```

### Command Line (Future Enhancement)

```bash
docutura convert input.pdf --format xlsx docx --theme indigenous
```

## Running Tests

```bash
pytest
```

**With coverage:**
```bash
pytest --cov=docutura --cov-report=html
```

## Verifying Installation

```python
# Test import
python -c "from docutura import __version__; print(f'DocTura {__version__} installed successfully')"
```

## Troubleshooting

### Issue: "pdfplumber" extraction errors
- Ensure PDF is not corrupted
- Try enabling OCR mode for scanned PDFs

### Issue: "pytesseract" not found
- Install Tesseract OCR (see above)
- Ensure it's in your system PATH

### Issue: Qt platform plugin errors (Windows)
- May need to install Microsoft Visual C++ Redistributable
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Issue: Permission errors on Windows
- Run terminal as Administrator
- Or install to user directory: `pip install --user -e .`

## Configuration

Default output directory: `~/Documents/DocTura/Output`
Default audit log directory: `~/Documents/DocTura/Audit`

These can be customized in the application settings (future enhancement).

## Updating

```bash
cd DOCTURA
git pull origin main
pip install -e .
```

## Uninstallation

```bash
pip uninstall docutura
```

## Support

For issues and questions, please visit:
https://github.com/bofe82frank/DOCTURA/issues
