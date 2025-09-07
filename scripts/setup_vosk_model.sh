#!/bin/bash

# Voxel Ambient Art Generator - Vosk Model Setup Script
# This script downloads and configures the Vosk speech recognition model

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
MODEL_DIR="models"
MODEL_NAME="vosk-model-en"
SMALL_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
SMALL_MODEL_FILE="vosk-model-small-en-us-0.15.zip"
SMALL_MODEL_EXTRACTED="vosk-model-small-en-us-0.15"

LARGE_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
LARGE_MODEL_FILE="vosk-model-en-us-0.22.zip"
LARGE_MODEL_EXTRACTED="vosk-model-en-us-0.22"

# Function to check available disk space
check_disk_space() {
    local required_space_mb=$1
    local available_space_mb=$(df . | tail -1 | awk '{print int($4/1024)}')
    
    print_status "Available disk space: ${available_space_mb}MB"
    print_status "Required disk space: ${required_space_mb}MB"
    
    if [ $available_space_mb -lt $required_space_mb ]; then
        print_error "Insufficient disk space. Required: ${required_space_mb}MB, Available: ${available_space_mb}MB"
        exit 1
    fi
    
    print_success "Sufficient disk space available"
}

# Function to check internet connectivity
check_internet() {
    print_status "Checking internet connectivity..."
    
    if ping -c 1 alphacephei.com >/dev/null 2>&1; then
        print_success "Internet connection verified"
    else
        print_error "No internet connection. Please check your network settings."
        exit 1
    fi
}

# Function to download and verify file
download_file() {
    local url=$1
    local filename=$2
    local expected_size_mb=$3
    
    print_status "Downloading $filename..."
    print_status "URL: $url"
    print_status "Expected size: ~${expected_size_mb}MB"
    
    # Download with progress bar
    if command -v wget >/dev/null 2>&1; then
        wget --progress=bar:force:noscroll -O "$filename" "$url"
    elif command -v curl >/dev/null 2>&1; then
        curl -L --progress-bar -o "$filename" "$url"
    else
        print_error "Neither wget nor curl is available. Please install one of them."
        exit 1
    fi
    
    # Verify download
    if [ -f "$filename" ]; then
        local actual_size_mb=$(du -m "$filename" | cut -f1)
        print_success "Download completed. Size: ${actual_size_mb}MB"
        
        # Basic size check (allow 10% variance)
        local min_size=$((expected_size_mb * 90 / 100))
        local max_size=$((expected_size_mb * 110 / 100))
        
        if [ $actual_size_mb -lt $min_size ] || [ $actual_size_mb -gt $max_size ]; then
            print_warning "Downloaded file size ($actual_size_mb MB) differs significantly from expected ($expected_size_mb MB)"
            print_warning "This might indicate a corrupted download"
        fi
    else
        print_error "Download failed. File not found: $filename"
        exit 1
    fi
}

# Function to extract and verify model
extract_model() {
    local zip_file=$1
    local extracted_dir=$2
    local target_dir=$3
    
    print_status "Extracting model from $zip_file..."
    
    # Check if unzip is available
    if ! command -v unzip >/dev/null 2>&1; then
        print_error "unzip command not found. Installing..."
        sudo apt update && sudo apt install -y unzip
    fi
    
    # Extract the model
    unzip -q "$zip_file"
    
    if [ -d "$extracted_dir" ]; then
        print_success "Model extracted successfully"
        
        # Move to target directory
        if [ -d "$target_dir" ]; then
            print_warning "Target directory $target_dir already exists. Removing..."
            rm -rf "$target_dir"
        fi
        
        mv "$extracted_dir" "$target_dir"
        print_success "Model moved to $target_dir"
        
        # Verify model structure
        verify_model_structure "$target_dir"
        
    else
        print_error "Extraction failed. Directory not found: $extracted_dir"
        exit 1
    fi
}

# Function to verify model structure
verify_model_structure() {
    local model_dir=$1
    
    print_status "Verifying model structure..."
    
    # Check for required files
    local required_files=(
        "am/final.mdl"
        "conf/mfcc.conf"
        "conf/model.conf"
        "graph/HCLG.fst"
        "graph/words.txt"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$model_dir/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        print_success "Model structure verified - all required files present"
    else
        print_error "Model structure verification failed. Missing files:"
        for file in "${missing_files[@]}"; do
            print_error "  - $file"
        done
        exit 1
    fi
    
    # Check file sizes
    local model_size=$(du -sh "$model_dir" | cut -f1)
    print_status "Model size: $model_size"
}

# Function to test model loading
test_model() {
    local model_dir=$1
    
    print_status "Testing model loading..."
    
    # Check if Python environment is available
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Skipping model test."
        return 0
    fi
    
    # Activate virtual environment and test
    source venv/bin/activate
    
    python3 -c "
import sys
import os
try:
    import vosk
    model_path = '$model_dir'
    if os.path.exists(model_path):
        model = vosk.Model(model_path)
        print('✓ Model loaded successfully')
        
        # Test recognizer creation
        rec = vosk.KaldiRecognizer(model, 16000)
        print('✓ Recognizer created successfully')
        
        # Test with dummy audio data
        import json
        dummy_audio = b'\\x00' * 3200  # 0.2 seconds of silence at 16kHz
        rec.AcceptWaveform(dummy_audio)
        result = rec.Result()
        parsed = json.loads(result)
        print('✓ Recognition test completed')
        
        print('Model test: PASSED')
    else:
        print('✗ Model path not found:', model_path)
        sys.exit(1)
except ImportError as e:
    print('✗ Vosk not installed:', e)
    sys.exit(1)
except Exception as e:
    print('✗ Model test failed:', e)
    sys.exit(1)
" || {
        print_error "Model test failed"
        exit 1
    }
    
    print_success "Model test passed"
}

# Function to setup small model (default)
setup_small_model() {
    print_status "Setting up small English model (91MB)..."
    print_status "This model is optimized for Raspberry Pi and provides good accuracy for most use cases."
    
    check_disk_space 200  # 200MB for download + extraction
    
    cd "$MODEL_DIR"
    
    # Download model
    download_file "$SMALL_MODEL_URL" "$SMALL_MODEL_FILE" 91
    
    # Extract model
    extract_model "$SMALL_MODEL_FILE" "$SMALL_MODEL_EXTRACTED" "$MODEL_NAME"
    
    # Clean up
    rm "$SMALL_MODEL_FILE"
    
    cd ..
    
    # Test model
    test_model "$MODEL_DIR/$MODEL_NAME"
    
    print_success "Small model setup completed successfully"
}

# Function to setup large model (advanced)
setup_large_model() {
    print_status "Setting up large English model (1.8GB)..."
    print_warning "This model provides better accuracy but requires more memory and processing power."
    print_warning "Recommended only for Raspberry Pi 4 with 8GB RAM or better hardware."
    
    check_disk_space 4000  # 4GB for download + extraction
    
    cd "$MODEL_DIR"
    
    # Download model
    download_file "$LARGE_MODEL_URL" "$LARGE_MODEL_FILE" 1800
    
    # Extract model
    extract_model "$LARGE_MODEL_FILE" "$LARGE_MODEL_EXTRACTED" "$MODEL_NAME"
    
    # Clean up
    rm "$LARGE_MODEL_FILE"
    
    cd ..
    
    # Test model
    test_model "$MODEL_DIR/$MODEL_NAME"
    
    print_success "Large model setup completed successfully"
}

# Function to remove existing model
remove_existing_model() {
    if [ -d "$MODEL_DIR/$MODEL_NAME" ]; then
        print_warning "Existing model found at $MODEL_DIR/$MODEL_NAME"
        read -p "Do you want to remove it and install a new one? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$MODEL_DIR/$MODEL_NAME"
            print_success "Existing model removed"
        else
            print_status "Keeping existing model. Exiting."
            exit 0
        fi
    fi
}

# Function to show model information
show_model_info() {
    echo
    print_status "Available Vosk Models:"
    echo
    echo "1. Small English Model (vosk-model-small-en-us-0.15)"
    echo "   - Size: ~91MB"
    echo "   - Memory usage: ~200MB"
    echo "   - Accuracy: Good for most conversations"
    echo "   - Recommended for: Raspberry Pi 4 (4GB+)"
    echo
    echo "2. Large English Model (vosk-model-en-us-0.22)"
    echo "   - Size: ~1.8GB"
    echo "   - Memory usage: ~500MB"
    echo "   - Accuracy: Excellent for all speech types"
    echo "   - Recommended for: Raspberry Pi 4 (8GB) or better"
    echo
}

# Main function
main() {
    echo
    print_status "🎤 Voxel Vosk Model Setup"
    echo "=========================="
    
    # Check if running from correct directory
    if [ ! -f "requirements.txt" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Create models directory
    mkdir -p "$MODEL_DIR"
    
    # Check internet connectivity
    check_internet
    
    # Check for existing model
    remove_existing_model
    
    # Show model options
    show_model_info
    
    # Get user choice
    while true; do
        read -p "Which model would you like to install? (1=Small [recommended], 2=Large, q=Quit): " choice
        case $choice in
            1|"")
                setup_small_model
                break
                ;;
            2)
                setup_large_model
                break
                ;;
            q|Q)
                print_status "Setup cancelled by user"
                exit 0
                ;;
            *)
                print_warning "Invalid choice. Please enter 1, 2, or q"
                ;;
        esac
    done
    
    echo
    print_success "🎉 Vosk model setup completed successfully!"
    echo
    print_status "Model location: $MODEL_DIR/$MODEL_NAME"
    print_status "You can now run the Voxel application with: python voxel.py"
    echo
}

# Run main function
main "$@"