# import os
# import cv2
# import face_recognition
# import pickle
# import subprocess
#
# def EG(image_path):
#
#     # Load existing encodings from file if available
#     encoding_file_path = 'EncodeFile.p'
#     if os.path.exists(encoding_file_path):
#         with open(encoding_file_path, 'rb') as file:
#             encodeListKnownWithNames = pickle.load(file)
#         encodeListKnown, empNames = encodeListKnownWithNames
#     else:
#         encodeListKnown = []
#         empNames = []
#
#     #Importing Employee Images
#     folderPath = 'Employee_Images'
#     pathlist = os.listdir(folderPath)
#     print(pathlist)
#
#     if not pathlist:
#         # Call the capture_image script using subprocess
#         subprocess.run(['python', 'webcam.py'], check=True)
#         # After capturing images, update the pathlist
#         pathlist = os.listdir(folderPath)
#
#     # # Proceed only if images are available
#     # if pathlist:
#     #     imgList = []
#     #     empNames = []
#     #
#     #     for path in pathlist:
#     #         imgList.append(cv2.imread(os.path.join(folderPath,path)))
#     #         empNames.append(os.path.splitext(path)[0])
#     #
#     #         # print(path)
#     #         # print(os.path.splitext(path)[0])
#     #
#     #     #Include the new image for encoding
#     #     new_img = cv2.imread(image_path)
#     #     imgList.append(new_img)
#     #     empNames.append(os.path.splitext(os.path.basename(image_path))[0])
#     #
#     #     print(len(imgList))
#     #     print(empNames)
#
#     imgList = []
#     empNames = []
#
#     # Map existing employee names to their encodings
#     #name_to_encoding = {name: encoding for name, encoding in zip(empNames, encodeListKnown)}
#
#     # Add the existing images from the folder
#     for path in pathlist:
#         imgList.append(cv2.imread(os.path.join(folderPath, path)))
#         empNames.append(os.path.splitext(path)[0])
#
#     # Only add the new image if it isn't already encoded
#     new_image_name = os.path.basename(image_path)
#     if new_image_name not in [os.path.basename(name) for name in empNames]:
#         imgList.append(cv2.imread(image_path))
#         empNames.append(os.path.splitext(new_image_name)[0])
#
#     #def findEncodings(images):
#     def findEncodings(imgList):
#         encodeList = []
#         #for img in images:
#         for img in imgList:
#             try:
#                 print(type(img))
#                 img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#                 encodings = face_recognition.face_encodings(img)
#                 if encodings:
#                     encodeList.append(encodings[0])
#                 else:
#                     print("No faces found in image.")
#             except Exception as e:
#                 print(f"Error processing image: {e}")
#         return encodeList
#
#     #For Genrating The Encode File
#     print("Encoding Started..........")
#     encodeListKnown = findEncodings(imgList)
#     encodeListKnownWithNames = [encodeListKnown, empNames]
#     print("Encodings:", encodeListKnown)
#     print("Encoding Ended............")
#
#     with open('EncodeFile.p', 'wb') as file:
#         pickle.dump(encodeListKnownWithNames, file)
#         file.close()
#     print("File Saved")






import os
import cv2
import face_recognition
import pickle
import subprocess


def findEncodings(images):
    encodeList = []
    for img in images:
        try:
            print(type(img))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(img)
            if encodings:
                encodeList.append(encodings[0])
            else:
                print("No faces found in image.")
        except Exception as e:
            print(f"Error processing image: {e}")
    print("Generated encodings:",encodeList)
    return encodeList

def EG(image_path):
    #print(f"Processing image: {image_path}")
    # Load existing encodings from file if available
    encoding_file_path = 'EncodeFile.p'

    if os.path.exists(encoding_file_path):
        with open(encoding_file_path, 'rb') as file:
            encodeListKnownWithNames = pickle.load(file)
        encodeListKnown, empNames = encodeListKnownWithNames
    else:
        encodeListKnown = []
        empNames = []

    # Importing Employee Images
    folderPath = 'Employee_Images'
    pathlist = os.listdir(folderPath)
    print(pathlist)

    if not pathlist:
        # Call the capture_image script using subprocess
        subprocess.run(['python', 'webcam.py'], check=True)
        # After capturing images, update the pathlist
        pathlist = os.listdir(folderPath)

    imgList = []
    #name_to_encoding = {name: encoding for name, encoding in zip(empNames, encodeListKnown)}

    # Check if the new image is already encoded
    new_image_name = os.path.splitext(os.path.basename(image_path))[0]

    if new_image_name not in empNames:
        imgList.append(cv2.imread(image_path))
        empNames.append(new_image_name)

    # Add existing images from the folder, but skip if already encoded
    for path in pathlist:
        emp_name = os.path.splitext(path)[0]
        if emp_name not in empNames:
            imgList.append(cv2.imread(os.path.join(folderPath, path)))
            empNames.append(emp_name)

    # Generate encodings only for new images
    if imgList:
        print("Encoding Started..........")
        try:
            new_encodings = findEncodings(imgList)
            encodeListKnown.extend(new_encodings)
        except Exception as e:
            print(f"Error during encoding: {e}")
            pass

        #print("Encodings:", encodeListKnown)
        print("Encoding Ended............")

        # Save the updated encodings and employee names
        encodeListKnownWithNames = [encodeListKnown, empNames]
        with open(encoding_file_path, 'wb') as file:
            pickle.dump(encodeListKnownWithNames, file)
        print("File Saved")

#IPTH = "Employee_Images/Varun_1.jpg"
#EG(IPTH)