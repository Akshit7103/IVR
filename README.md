# IVR Agent - Fraud Detection System

An automated Interactive Voice Response (IVR) system for detecting and managing fraudulent transactions. The system uses Twilio's voice API to call customers and verify suspicious transactions through an automated conversational flow.

## Features

- **Automated Fraud Detection Calls**: Initiates voice calls to customers for suspicious transactions
- **Multi-step Verification Flow**: Guides customers through a series of questions to verify transactions
- **Real-time Dashboard**: Web-based interface to monitor and manage transactions
- **Transaction Management**: Update phone numbers, trigger calls, and track call statuses
- **Smart Call Routing**: Handles different outcomes (confirmed, denied, physical/virtual card preferences)
- **Status Tracking**: Monitors call statuses including resolved, fraud, disconnected, and not answered

## Project Structure

```
IVR/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── data/
│   └── transactions.json       # Transaction data storage
├── templates/
│   └── index.html             # Dashboard HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Dashboard styles
│   └── js/
│       └── main.js            # Frontend JavaScript
├── Script.txt                 # IVR conversation script reference
└── README.md                  # This file
```

## Prerequisites

- Python 3.8 or higher
- Twilio account with:
  - Account SID
  - Auth Token
  - Twilio phone number
- ngrok (for local development)

## Installation

### 1. Clone or Download the Project

```bash
cd IVR
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
# Twilio Credentials
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_NUMBER=your_twilio_phone_number

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here-change-in-production

# Public URL (will be set by ngrok)
PUBLIC_URL=https://your-ngrok-url.ngrok.io
```

**How to get Twilio credentials:**
1. Sign up at [https://www.twilio.com](https://www.twilio.com)
2. Navigate to Console Dashboard
3. Copy your Account SID and Auth Token
4. Purchase a phone number from Twilio Console

## Running the Application

### Step 1: Start the Flask Application

```bash
python app.py
```

The application will start on `http://0.0.0.0:5000`

### Step 2: Set Up ngrok Tunnel

In a **new terminal window**, run:

```bash
ngrok http 5000
```

You should see output like:

```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

### Step 3: Update PUBLIC_URL

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`) and update it in your `.env` file:

```env
PUBLIC_URL=https://abc123.ngrok.io
```

Then **restart the Flask application** for changes to take effect.

### Step 4: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage Guide

### Dashboard Features

1. **View Transactions**: See all transactions in a tabular format with details like:
   - Transaction ID
   - Client Name
   - Card Number
   - Phone Number
   - Amount
   - Bank Name
   - Merchant Name
   - Transaction Date
   - Current Status

2. **Edit Phone Numbers**: Click on any phone number field to edit it. Changes save automatically.

3. **Initiate Calls**: Click on the status badge to trigger an automated call to the customer.

4. **Search**: Use the search bar to filter transactions by any field.

5. **Auto-refresh**: Dashboard automatically polls for updates every 5 seconds.

### Call Flow

When a call is initiated, the system follows this conversation flow:

1. **Step 0 - Initial Confirmation**
   - Greets customer with transaction details
   - Asks: "Did you authorize this transaction?"
   - **Yes** → Marks as "Resolved" and ends call
   - **No** → Proceeds to Step 1

2. **Step 1 - Card Details Sharing**
   - Asks: "Have you shared your card details with anyone?"
   - Proceeds to Step 2 regardless of answer

3. **Step 2 - Other Suspicious Transactions**
   - Asks: "Have you noticed any other suspicious transactions?"
   - Proceeds to Step 3 regardless of answer

4. **Step 3 - Inform Block Action**
   - Informs customer: "We will block this transaction and issue a new card"
   - Proceeds to Step 4

5. **Step 4 - Card Delivery Preference**
   - Asks: "Physical card or virtual card?"
   - **Physical** → Steps 5, 6, 7
   - **Virtual** → Step 8

6. **Step 5 - Physical Card Timeline** (if physical selected)
   - Informs: "Card will arrive in 3-5 business days"

7. **Step 6 - Virtual Card Issuance** (with physical)
   - Informs: "Meanwhile, virtual card issued via mobile app"

8. **Step 7 - Fraud Case Confirmation** (physical path)
   - Marks transaction as "Mark As Fraud"
   - Confirms fraud case logged
   - Ends call

9. **Step 8 - Virtual Only Path**
   - Marks transaction as "Mark As Fraud"
   - Informs virtual card issued
   - Confirms fraud case logged
   - Ends call

### Status Indicators

- **Resolved**: Customer confirmed the transaction
- **Mark As Fraud**: Customer denied transaction, fraud case created
- **Connecting**: Call is being initiated
- **Not Answered**: Customer did not answer the call
- **Disconnected**: Call failed or was disconnected
- **Clickable badges**: Click to initiate call (except when Resolved or Connecting)

## API Endpoints

### Web Routes
- `GET /` - Main dashboard
- `GET /transactions` - Get all transactions (JSON)

### Transaction Management
- `POST /update_phone/<txn_id>` - Update customer phone number
- `POST /set_action/<txn_id>` - Update transaction action status

### Call Control
- `POST /call/<txn_id>` - Initiate call for a transaction
- `POST /status/<txn_id>` - Webhook for call status updates

### Voice Flow (Twilio Webhooks)
- `POST /voice/<txn_id>/step0` - Initial greeting and confirmation
- `POST /voice/<txn_id>/step0/response` - Process initial response
- `POST /voice/<txn_id>/step1` - Card details question
- `POST /voice/<txn_id>/step1/response` - Process card details response
- `POST /voice/<txn_id>/step2` - Other suspicious transactions
- `POST /voice/<txn_id>/step2/response` - Process step 2 response
- `POST /voice/<txn_id>/step3` - Inform about blocking action
- `POST /voice/<txn_id>/step4` - Card preference question
- `POST /voice/<txn_id>/step4/response` - Process card preference
- `POST /voice/<txn_id>/step5` - Physical card timeline
- `POST /voice/<txn_id>/step6` - Virtual card issuance (with physical)
- `POST /voice/<txn_id>/step7` - Fraud case confirmation (physical)
- `POST /voice/<txn_id>/step8` - Virtual only path completion

## Configuration

### Twilio Speech Recognition Settings

The system uses:
- **Language**: English (India) - `en-IN`
- **Input**: Speech
- **Timeout**: 5 seconds
- **Speech Timeout**: 1 second
- **Hints**: Common responses (yes, no, yeah, nope, physical, virtual)
- **Retry Logic**: Up to 2 retries per step

### Data Persistence

Transactions are stored in `data/transactions.json`. The file is read/written for each operation to ensure data persistence.

## Troubleshooting

### Common Issues

1. **Calls not connecting**
   - Verify Twilio credentials in `.env`
   - Ensure PUBLIC_URL is set to your ngrok HTTPS URL
   - Check that ngrok tunnel is active
   - Verify phone numbers are in correct format (E.164: +1234567890)

2. **ngrok session expired**
   - Free ngrok URLs change on restart
   - Update PUBLIC_URL in `.env` with new ngrok URL
   - Restart Flask application

3. **Speech recognition issues**
   - Ensure clear audio input
   - Check Twilio console logs for transcription results
   - Adjust hints in gather configuration if needed

4. **Dashboard not updating**
   - Check browser console for errors
   - Verify Flask server is running
   - Check network tab for failed API calls

## Development

### Adding New Transaction Fields

1. Update `data/transactions.json` with new fields
2. Modify `templates/index.html` to display new columns
3. Update `static/css/style.css` for styling
4. Adjust `app.py` if new API endpoints are needed

### Customizing Call Script

1. Edit the script in respective `/voice/<txn_id>/stepX` endpoints
2. Modify speech hints for better recognition
3. Adjust timeout values as needed
4. Update retry logic if required

### Testing

To test without making actual calls:
1. Use Twilio's test credentials (starts with `AC`)
2. Check Twilio logs in Console Dashboard
3. Use browser developer tools to monitor API calls
4. Review Flask console output for debugging

## Security Considerations

- **Never commit `.env` file** - Add to `.gitignore`
- **Change FLASK_SECRET_KEY** in production
- **Use HTTPS** for all Twilio webhooks
- **Validate phone numbers** before initiating calls
- **Implement rate limiting** for production use
- **Add authentication** for dashboard access
- **Sanitize user inputs** in phone number fields

## Technologies Used

- **Backend**: Flask (Python)
- **Voice API**: Twilio
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Storage**: JSON file-based
- **Tunneling**: ngrok
- **Environment Management**: python-dotenv

## License

This project is provided as-is for educational and development purposes.

## Support

For issues related to:
- **Twilio**: Visit [Twilio Support](https://support.twilio.com)
- **ngrok**: Visit [ngrok Documentation](https://ngrok.com/docs)
- **Application bugs**: Check console logs and review the code

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Author

Created for fraud detection automation using IVR technology.

## Acknowledgments

- Twilio for Voice API
- ngrok for secure tunneling
- Flask framework community
