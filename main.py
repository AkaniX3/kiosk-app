from flask import Flask, jsonify, session, request, send_file
from zipfile import ZipFile
import os
import razorpay
from dotenv import load_dotenv
from flask_cors import CORS

#getting them statically
# load_dotenv(dotenv_path=".env", verbose=True, override=True)
# key_id = os.environ.get('key_id')
# key_secret = os.environ.get('key_secret')
key_id='rzp_test_eINCFzPCyiSQFx'
key_secret='7bUE8FtB2Iydjo0JNVpM8RZ2'

app = Flask(__name__)
# app.secret_key = 'your_secret_key'

UPLOAD_DIRECTORY = 'user_uploads'
app.config['UPLOAD_DIRECTORY']=UPLOAD_DIRECTORY
# os.makedirs(app.config['UPLOAD_DIRECTORY'], exist_ok=True)

CORS(app, resources={r"*": {"origins": "*"}})

client=razorpay.Client(auth=(key_id,key_secret))

def create_zip(folder_path, zip_filename):
    # Get a list of all files in the folder
    all_files = os.listdir(folder_path)

    # Create a zip archive containing all files
    with ZipFile(zip_filename, 'w') as zip_file:
        for file in all_files:
            file_path = os.path.join(folder_path, file)
            zip_file.write(file_path, file)

@app.route('/')
def index():
    return "Working Main Server"

@app.route('/payment',methods=['POST'])
def check_out():
    
    amount = request.json.get('value')
    data={
        'amount':amount*100,
        'currency':"INR",
        'receipt':'Print Kiosk',
        'notes':{
            'name':"Print Kiosk",
            "Payment_for":"Print(s)",
            
        }
    }

    try:
        order = client.order.create(data=data)
        order_id = order['id']
        return jsonify({'order_id': order_id, 'key_id': key_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@app.route('/verify', methods=['POST'])
def verifying():
    
    payment_data = request.json
    print(payment_data)
    try:
        client.utility.verify_payment_signature(payment_data)
        print('\n **** Payment Successful ****\n')
    except Exception as e:
        print("\n **** Payment Failed ****\n",e)
    return "Payment Success"


def delete_uploaded_files():
    # Delete all files from the user_uploads directory
    for filename in os.listdir(UPLOAD_DIRECTORY):
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

@app.route('/startSession', methods=['POST'])
def start_session():
    # Start a session for the kiosk
    session['session_started'] = True
    return jsonify({'message': 'Session started successfully.'}), 200

@app.route('/endSession', methods=['GET'])
def end_session():
    # Clear the session data
    #COMMENTNING THIS
    # session.clear()
    delete_uploaded_files()
    os.remove('my_files.zip')
    # Call the function to delete uploaded files
    return jsonify({'message': 'Session ended successfully. Uploaded files deleted.', 'status_code': '200'})

@app.route('/upload', methods=['POST'])
def upload_files():
    
    if 'pdfFiles' not in request.files:
        print("NO FILES UPLOADED")
        return jsonify({'error': 'No files provided.'}), 400
    
    uploaded_files = request.files.getlist('pdfFiles')
    os.makedirs(app.config['UPLOAD_DIRECTORY'], exist_ok=True)


    for file in uploaded_files:
        file.save(os.path.join(app.config['UPLOAD_DIRECTORY'], file.filename))
        
    folder_to_zip = app.config['UPLOAD_DIRECTORY']  # Specify the folder containing your files
    zip_filename = 'my_files.zip'  # Choose a name for your zip file
    try:
        create_zip(folder_to_zip, zip_filename)
    except Exception as e:
        print (e)
    delete_uploaded_files()
    return jsonify({'message': 'Files uploaded successfully.'}), 200

@app.route('/download_file', methods=['GET'])
def download_files():
    # Get a list of all files in the directory
    # all_files = os.listdir(app.config['UPLOAD_DIRECTORY'])

    # # Check if any files exist in the directory
    # if not all_files:
    #     print("NOT RECEIVED")
    #     return jsonify({'error': 'No files to download.'}), 404
    # print(all_files)
    # # Create a zip archive containing all files
    # zip_path = 'my_files.zip'
    existing_zip_path = 'my_files.zip'

    # Check if the file exists
    if not os.path.exists(existing_zip_path):
        return jsonify({'error': 'The specified zip file does not exist.'}), 404

    # Send the zip file as an attachment
    try:
        return send_file(existing_zip_path, as_attachment=True, download_name='existing.zip')
    except Exception as e:
        return jsonify({'error': 'Error downloading the file.'}), 500
    
    # with ZipFile(zip_path, 'w') as zip_file:
    #     for file in all_files:
    #         file_path = os.path.join(UPLOAD_DIRECTORY, file)
    #         print(f"Zipping file: {file_path}")

    #         zip_file.write(file_path, file)


    # Serve the zip archive
    # try:
    #     with open(zip_path, 'rb') as f:
    #         return send_file(f, as_attachment=True, download_name='files.zip')
    
    #    #return send_file(zip_path, as_attachment=True)
    # except Exception as e:
    #     print("ERROR DOWNLOADING")
    #     return jsonify({'error': f'Error downloading files: {str(e)}'}), 500
    # #finally:
    #     # Delete the zip archive after serving
        #os.remove(zip_path)

#PAYMENT



if __name__ == '__main__':
    app.run(port=5002, debug=True)
