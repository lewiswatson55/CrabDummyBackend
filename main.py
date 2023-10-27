import json
import zipfile

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import datetime

app = Flask(__name__)


@app.route('/list', methods=['GET'])
@app.route('/', methods=['GET'])
def list_submissions():
    submission_files = []  # List to hold all submission files info
    base_directory = 'requests/submissions'  # Base directory where submissions are stored

    # Loop to walk through directories and subdirectories
    for dirpath, dirnames, filenames in os.walk(base_directory):
        for filename in filenames:
            if filename.endswith(''):  # Assuming the submissions are in JSON format
                relative_path = os.path.join(dirpath, filename)
                submission_files.append({
                    'name': filename,
                    'path': relative_path
                })

    return render_template('list.html', submission_files=submission_files)


@app.route('/details/<path:file_path>', methods=['GET'])
def submission_details(file_path):
    is_json = True  # Flag to check if the file is JSON
    try:
        # Read the raw file content
        with open(file_path, 'r') as f:
            raw_content = f.read()

        # Attempt to parse the file content as JSON
        try:
            content = json.loads(raw_content)
            pretty_content = json.dumps(content, indent=4)  # Pretty-print the JSON content
        except json.JSONDecodeError:
            is_json = False  # Set flag to False if parsing fails
            pretty_content = raw_content  # Display the raw content

    except Exception as e:
        return f"An error occurred: {e}", 500

    return render_template('details.html', file_content=pretty_content, is_json=is_json)



@app.route('/delete_submission/<path:file_path>', methods=['get','POST'])
def delete_submission(file_path):
    try:
        # Ensure the path is safe to delete
        safe_base_directory = os.path.abspath('requests/submissions')
        safe_file_path = os.path.abspath(file_path)

        if not safe_file_path.startswith(safe_base_directory):
            return "Unauthorized action", 403

        os.remove(safe_file_path)
        return redirect(url_for('list_submissions'))
    except Exception as e:
        return f"An error occurred while deleting the file: {e}", 500

@app.route('/generate_dummy', methods=['POST'])
def generate_dummy():
    dummy_content = '{"sightings":[{"valid":true,"seen_by":"123456-123456-654321-654321","answers":[{"0":["1.0"],"1":["0"],"2":["0"],"3":["0"],"4":["0"],"5":["08/01/2016 00:00"],"6":["Bahia"],"7":["Caravelas"],"8":["• Não quero informar"],"9":["20 de nov. de 2020 14:20:22"]}]}]}'
    save_request(dummy_content, subdirectory='submissions')
    return redirect(url_for('list_submissions'))



# Submission Endpoint
@app.route('/submission', methods=['GET', 'POST'])
def submission():
    if request.method == 'POST':
        # dump
        save_request(request.data, subdirectory='submissions')
        return "Submission received", 200
    else:
        return "This endpoint is for submissions only - also ensure you are using a POST request", 405

# Function to save incoming request data to a file for logs
def save_request(request_data, subdirectory='request_logs'):
    print("Received request data:", request_data)

    id = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))

    # Get current month and year
    current_month = datetime.datetime.now().strftime("%B")
    current_year = datetime.datetime.now().strftime("%Y")

    # Create subdirectory if it doesn't exist under the base directory
    base_directory = 'requests'
    subdirectory_path = os.path.join(base_directory, subdirectory)
    if not os.path.exists(subdirectory_path):
        os.makedirs(subdirectory_path)

    # Create year directory if it doesn't exist under the subdirectory
    year_directory = os.path.join(subdirectory_path, current_year)
    if not os.path.exists(year_directory):
        os.makedirs(year_directory)

    # Create month directory if it doesn't exist under the year directory
    month_directory = os.path.join(year_directory, current_month)
    if not os.path.exists(month_directory):
        os.makedirs(month_directory)

    # Save the request data to a file
    file_path = os.path.join(month_directory, "{}.json".format(id))
    with open(file_path, 'w') as f:
        f.write(str(request_data))

    return 0

@app.route('/download_all', methods=['GET'])
def download_all():
    # Define the name of the output ZIP file
    zip_filename = 'all_submissions.zip'
    zip_full_path = os.path.join('requests', zip_filename)

    # Create a new ZIP file (overwrite if it exists)
    with zipfile.ZipFile(zip_full_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk the submissions folder and add each file to the ZIP
        for root, _, files in os.walk('requests/submissions'):
            for file in files:
                absolute_path = os.path.join(root, file)
                relative_path = os.path.relpath(absolute_path, 'requests/submissions')
                zipf.write(absolute_path, relative_path)

    # Serve the ZIP file for download
    return send_from_directory('requests', zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

