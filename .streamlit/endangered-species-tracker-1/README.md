# Endangered Species Tracker

## Overview
The Endangered Species Tracker is a Streamlit application designed to visualize and track endangered species data sourced from Google Sheets. The application utilizes the Google Sheets API to securely load data while ensuring that access is restricted to authorized users only.

## Project Structure
```
endangered-species-tracker
├── app.py                # Main entry point for the Streamlit application
├── data_loader.py        # Contains functions for loading data from Google Sheets
├── requirements.txt      # Lists required Python packages
├── .env.example          # Template for environment variables
└── README.md             # Documentation for the project
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd endangered-species-tracker
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Requirements**
   Install the necessary packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

4. **Google Sheets API Setup**
   - Create a Google Cloud project and enable the Google Sheets API.
   - Create a Service Account and download the `credentials.json` file.
   - Share your Google Sheet with the Service Account email to grant access.

5. **Environment Variables**
   - Copy `.env.example` to `.env` and fill in any necessary configurations for local development.

## Usage Guidelines
- Run the application using the following command:
  ```bash
  streamlit run app.py
  ```
- The application will load data from the specified Google Sheet and display it in a user-friendly format, including graphs and visuals.

## Functionality
- The application connects to Google Sheets using a Service Account for secure data access.
- Data is loaded and displayed in a visually appealing manner, utilizing a color scheme of purple, black, white, and blue.
- Error handling is implemented to provide clear feedback in case of authentication issues or data loading failures.
- Data loading is optimized with caching to enhance performance.

## Contribution
Contributions to the Endangered Species Tracker project are welcome. Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.