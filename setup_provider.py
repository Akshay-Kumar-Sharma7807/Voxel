#!/usr/bin/env python3
"""
Provider setup script for Voxel image generation.
Supports OpenAI, Google Cloud, and Freepik AI.
"""

import os
import sys
from pathlib import Path


def setup_openai():
    """Setup OpenAI DALL-E provider."""
    print("=== OpenAI DALL-E Setup ===")
    print("Features: High-quality images, reliable API, $0.04 per image")
    
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["IMAGE_PROVIDER"] = "openai"
    
    print("✅ OpenAI provider configured")
    print("Environment variables set:")
    print(f"  OPENAI_API_KEY: {api_key[:8]}...")
    print(f"  IMAGE_PROVIDER: openai")
    
    return True


def setup_google_cloud():
    """Setup Google Cloud Vertex AI provider."""
    print("=== Google Cloud Vertex AI Setup ===")
    print("Features: Enterprise-grade, $0.02 per image, scalable")
    
    project_id = input("Enter your GCP Project ID: ").strip()
    if not project_id:
        print("❌ No project ID provided")
        return False
    
    credentials_path = input("Enter path to service account JSON (or press Enter for default auth): ").strip()
    location = input("Enter GCP location (default: us-central1): ").strip() or "us-central1"
    
    # Set environment variables
    os.environ["GCP_PROJECT_ID"] = project_id
    os.environ["GCP_LOCATION"] = location
    os.environ["IMAGE_PROVIDER"] = "google_cloud"
    
    if credentials_path:
        if Path(credentials_path).exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"✅ Using service account: {credentials_path}")
        else:
            print(f"⚠️  Credentials file not found: {credentials_path}")
            print("Will use default authentication")
    else:
        print("✅ Using default Google Cloud authentication")
    
    print("✅ Google Cloud provider configured")
    print("Environment variables set:")
    print(f"  GCP_PROJECT_ID: {project_id}")
    print(f"  GCP_LOCATION: {location}")
    print(f"  IMAGE_PROVIDER: google_cloud")
    
    return True


def setup_freepik():
    """Setup Freepik AI provider."""
    print("=== Freepik AI Setup ===")
    print("Features: High-quality images, multiple styles, competitive pricing")
    
    api_key = input("Enter your Freepik API key: ").strip()
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Set environment variables
    os.environ["FREEPIK_API_KEY"] = api_key
    os.environ["IMAGE_PROVIDER"] = "freepik"
    
    print("✅ Freepik provider configured")
    print("Environment variables set:")
    print(f"  FREEPIK_API_KEY: {api_key[:8]}...")
    print(f"  IMAGE_PROVIDER: freepik")
    
    return True


def show_provider_comparison():
    """Show comparison of all providers."""
    print("\n📊 Provider Comparison:")
    print("┌─────────────────┬──────────────┬─────────────┬──────────────────┐")
    print("│ Provider        │ Cost/Image   │ Quality     │ Best For         │")
    print("├─────────────────┼──────────────┼─────────────┼──────────────────┤")
    print("│ OpenAI DALL-E   │ ~$0.04       │ Excellent   │ General purpose  │")
    print("│ Google Cloud    │ ~$0.02       │ Excellent   │ Enterprise/Scale │")
    print("│ Freepik AI      │ ~$0.01-0.03  │ Very Good   │ Creative/Artistic│")
    print("└─────────────────┴──────────────┴─────────────┴──────────────────┘")
    
    print("\n🔍 Detailed Features:")
    print("\n🤖 OpenAI DALL-E 3:")
    print("  ✅ Highest quality and consistency")
    print("  ✅ Best prompt understanding")
    print("  ✅ Most reliable API")
    print("  ❌ Most expensive")
    print("  ❌ Rate limits on free tier")
    
    print("\n☁️  Google Cloud Vertex AI:")
    print("  ✅ Enterprise-grade infrastructure")
    print("  ✅ Lower cost than OpenAI")
    print("  ✅ Excellent scalability")
    print("  ❌ Complex setup")
    print("  ❌ Requires GCP account")
    
    print("\n🎨 Freepik AI:")
    print("  ✅ Great for creative/artistic content")
    print("  ✅ Multiple models and styles")
    print("  ✅ Competitive pricing")
    print("  ✅ Fast generation")
    print("  ❌ Newer API (less mature)")
    print("  ❌ Requires subscription for API access")


def main():
    """Main setup function."""
    print("🎨 Voxel Image Provider Setup\n")
    
    show_provider_comparison()
    
    print("\n🚀 Available providers:")
    print("1. OpenAI DALL-E 3 (Premium quality)")
    print("2. Google Cloud Vertex AI (Enterprise)")
    print("3. Freepik AI (Creative & Affordable)")
    print("4. Show detailed comparison")
    
    choice = input("\nSelect provider (1-4): ").strip()
    
    success = False
    if choice == "1":
        success = setup_openai()
    elif choice == "2":
        success = setup_google_cloud()
    elif choice == "3":
        success = setup_freepik()
    elif choice == "4":
        show_provider_comparison()
        return main()  # Show menu again
    else:
        print("❌ Invalid choice")
        return
    
    if success:
        print(f"\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Run the web app: python app.py")
        print("2. Open browser to: http://localhost:5000")
        print("3. Click 'Start Listening' to test image generation")
        
        # Show provider-specific tips
        provider = os.environ.get("IMAGE_PROVIDER")
        if provider == "openai":
            print("\n💡 OpenAI Tips:")
            print("- Monitor usage to avoid unexpected charges")
            print("- Consider upgrading for higher rate limits")
        elif provider == "google_cloud":
            print("\n💡 Google Cloud Tips:")
            print("- Set up billing alerts")
            print("- Monitor quotas in GCP Console")
            print("- Consider regional deployment")
        elif provider == "freepik":
            print("\n💡 Freepik Tips:")
            print("- Experiment with different models (flux, flux-realism)")
            print("- Try various styles for different moods")
            print("- Monitor API usage in Freepik dashboard")
        
        # Offer to test the setup
        test = input("\nTest the setup now? (y/n): ").strip().lower()
        if test == 'y':
            print("Starting web application...")
            os.system("python app.py")


if __name__ == "__main__":
    main()