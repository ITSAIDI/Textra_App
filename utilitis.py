import streamlit as st
from paddleocr import PaddleOCR
from PIL import ImageDraw, ImageFont,ImageEnhance
import torch
from transformers import AutoProcessor,LayoutLMv3ForTokenClassification
import numpy as np
import time
import pyrebase
from io import BytesIO
import os
import json

model_Hugging_path = "Noureddinesa/Output_LayoutLMv3_v7"

def Paddle():
    ocr = PaddleOCR(use_angle_cls=False,lang='fr',rec=False,use_gpu =True)
    return ocr

#############################################################################
#############################################################################
def Labels():
    labels = ['InvNum', 'InvDate', 'Fourni', 'TTC', 'TVA', 'TT', 'Autre']
    id2label = {v: k for v, k in enumerate(labels)}
    label2id = {k: v for v, k in enumerate(labels)}
    return id2label, label2id


def processbbox(BBOX, width, height):
    bbox = []
    bbox.append(BBOX[0][0])
    bbox.append(BBOX[0][1])
    bbox.append(BBOX[2][0])
    bbox.append(BBOX[2][1])
    #Scaling
    bbox[0]= 1000*bbox[0]/width # X1
    bbox[1]= 1000*bbox[1]/height # Y1
    bbox[2]= 1000*bbox[2]/width # X2
    bbox[3]= 1000*bbox[3]/height # Y2
    for i in range(4):
        bbox[i] = int(bbox[i])
    return bbox


def Preprocess(image):
    ocr = Paddle()
    image_array = np.array(image)
    width, height = image.size
    results = ocr.ocr(image_array,  cls=False,rec = True)
    results = results[0]
    test_dict = {'image': image ,'tokens':[], "bboxes":[]}
    for item in results :
       bbox = processbbox(item[0], width, height)
       test_dict['tokens'].append(item[1][0])
       test_dict['bboxes'].append(bbox)

    print(test_dict['bboxes'])
    print(test_dict['tokens'])
    return test_dict

#############################################################################
#############################################################################
def Encode(image):
    example = Preprocess(image)
    image = example["image"]
    words = example["tokens"]
    boxes = example["bboxes"]
    processor = AutoProcessor.from_pretrained(model_Hugging_path, apply_ocr=False)
    encoding = processor(image, words, boxes=boxes,return_offsets_mapping=True,truncation=True, max_length=512, padding="max_length", return_tensors="pt")
    offset_mapping = encoding.pop('offset_mapping')
    return encoding, offset_mapping,words
#############################################################################
#############################################################################
def unnormalize_box(bbox, width, height):
     return [
         width * (bbox[0] / 1000),
         height * (bbox[1] / 1000),
         width * (bbox[2] / 1000),
         height * (bbox[3] / 1000),
     ]

def drop_null_bbox(dictionary):
    keys_to_drop = []
    for key, (_, _, bbox_values) in dictionary.items():
        if all(value == 0.0 for value in bbox_values):
            keys_to_drop.append(key)
    for key in keys_to_drop:
        del dictionary[key]

def get_word(bboxes,image):
    ocr = Paddle()
    x_min, y_min, x_max, y_max = bboxes
    roi = image.crop((x_min, y_min, x_max, y_max)) # Region of intrest
    roi_np = np.array(roi) # To array
    result = ocr.ocr(roi_np, cls=False,det = False,rec = True)
    if result != [None]:
        return result[0][0][0]
    else :
        return ""
#############################################################################
#############################################################################  
def get_Finale_results(offset_mapping,id2label,image,prediction_scores,predictions,token_boxes):
    width, height = image.size
    is_subword = np.array(offset_mapping.squeeze().tolist())[:,0] != 0
    # Filter out subword tokens and extract true predictions and scores
    true_predictions_with_scores = [(idx,id2label[pred], score[pred],unnormalize_box(box, width, height)) for idx, (pred, score,box) in enumerate(zip(predictions, prediction_scores,token_boxes)) if not is_subword[idx]]
    Final_prediction = [pred for pred in true_predictions_with_scores if pred[1] != "Autre"]
    # Create a dictionary to store the highest score for each prediction
    Final_results = {}
    # Eliminete Duplication of Predictions
    for index, prediction, score, bbox in Final_prediction:
        if prediction not in Final_results or score > Final_results[prediction][1]:
            Final_results[prediction] = (index, score,bbox)
    drop_null_bbox(Final_results)
    
    for final in Final_results:
        Kalma = get_word(Final_results[final][2],image)
        New_tuple = (Kalma,Final_results[final][1],Final_results[final][2])
        Final_results[final] = New_tuple
    
    return Final_results

def Run_model(image):
    encoding,offset_mapping,_ = Encode(image)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # load the fine-tuned model from the hub
    model = LayoutLMv3ForTokenClassification.from_pretrained(model_Hugging_path)
    model.to(device)
    # forward pass
    outputs = model(**encoding)
    
    prediction_scores = outputs.logits.softmax(-1).squeeze().tolist()
    predictions = outputs.logits.argmax(-1).squeeze().tolist()
    token_boxes = encoding.bbox.squeeze().tolist()
    id2label, _ = Labels()
    Finale_results=get_Finale_results(offset_mapping,id2label,image,prediction_scores,predictions,token_boxes)
    return Finale_results
    
#############################################################################
#############################################################################
def Get_Dict(Finale_results):
    Results = {}
    for prd in Finale_results:
        if prd in ['InvNum','Fourni', 'InvDate','TT','TTC','TVA']:
            
            if prd in ['TT','TTC','TVA']:
                Results[prd] = clean_text(Finale_results[prd][0])
            else :
                Results[prd] = Finale_results[prd][0]

    key_mapping = {'InvNum':'Numéro de facture','Fourni':'Fournisseur', 'InvDate':'Date Facture','TT':'Total HT','TTC':'Total TTC','TVA':'TVA'}
    Results = {key_mapping.get(key, key): value for key, value in Results.items()}
    return Results
      
#############################################################################
#############################################################################   
def Draw(image):
    start_time = time.time()
    
    image = enhance_image(image,1.3,1.7)
    Finale_results = Run_model(image)
    draw = ImageDraw.Draw(image)
    label2color = {
        'InvNum': 'blue',
        'InvDate': 'green',
        'Fourni': 'orange',
        'TTC':'purple',
        'TVA': 'magenta',
        'TT': 'red',
        'Autre': 'black'
    }

    # Adjust the thickness of the rectangle outline and label text position
    rectangle_thickness = 4
    label_x_offset = 20
    label_y_offset = -30
    # Custom font size
    custom_font_size = 25

    # Load a font with the custom size
    font_path = "arial.ttf"  # Specify the path to your font file
    custom_font = ImageFont.truetype(font_path, custom_font_size)

    for result in Finale_results:
        predicted_label = result
        box = Finale_results[result][2]
        color = label2color[result]
        draw.rectangle(box, outline=color, width=rectangle_thickness)
        #print(box)
        # Draw text using the custom font and size
        draw.rectangle((box[0], box[1]+ label_y_offset,box[2],box[3]+ label_y_offset), fill=color)
        draw.text((box[0] + label_x_offset, box[1] + label_y_offset), text=predicted_label, fill='white', font=custom_font)
    
    Results = Get_Dict(Finale_results)
    end_time = time.time() 
    execution_time = end_time - start_time 
    
    return image,Results,execution_time


#############################################################################
#############################################################################

def Update(Results,Coin):
    New_results = {}

    if "Fournisseur" in Results.keys():
        text_fourni = st.sidebar.text_input("Fournisseur", value=Results["Fournisseur"])
        New_results["Fournisseur"] = text_fourni
    else : 
        text_fourni = st.sidebar.text_input("Fournisseur", value= "")
        New_results["Fournisseur"] = text_fourni
        
    if "Date Facture" in Results.keys():
        text_InvDate = st.sidebar.text_input("Date Facture", value=Results["Date Facture"])
        New_results["Date Facture"] = text_InvDate
    else : 
        text_InvDate = st.sidebar.text_input("Date Facture", value= "")
        New_results["Date Facture"] = text_InvDate
        
    if "Numéro de facture" in Results.keys():
        text_InvNum = st.sidebar.text_input("Numéro de facture", value=Results["Numéro de facture"])
        New_results["Numéro de facture"] = text_InvNum
    else : 
        text_InvNum = st.sidebar.text_input("Numéro de facture", value= "")
        New_results["Numéro de facture"] = text_InvNum
        
    if "Total HT" in Results.keys():
        text_TT = st.sidebar.text_input("Total HT", value=Results["Total HT"])
        New_results["Total HT"] = text_TT + " " +Coin
    else : 
        text_TT = st.sidebar.text_input("Total HT", value= "")
        New_results["Total HT"] = text_TT + " " +Coin
        
    if "TVA" in Results.keys():
        text_TVA = st.sidebar.text_input("TVA", value=Results["TVA"])
        New_results["TVA"] = text_TVA + " " +Coin
    else : 
        text_TVA = st.sidebar.text_input("TVA", value= "")
        New_results["TVA"] = text_TVA+ " " +Coin
        
    if "Total TTC" in Results.keys():
        text_TTC = st.sidebar.text_input("Total TTC", value=Results["Total TTC"])
        New_results["Total TTC"] = text_TTC + " " +Coin
    else : 
        text_TTC = st.sidebar.text_input("Total TTC", value= "")
        New_results["Total TTC"] = text_TTC+ " " +Coin
        
    return New_results

#############################################################################
#############################################################################
def Change_Image(image1,image2):
        # Initialize session state
        if 'current_image' not in st.session_state:
            st.session_state.current_image = 'image1'

        # Button to switch between images
        if st.sidebar.button('Switcher'):
            if st.session_state.current_image == 'image1':
                st.session_state.current_image = 'image2'
            else:
                st.session_state.current_image = 'image1'
        # Display the selected image
        if st.session_state.current_image == 'image1':
            st.image(image1, caption='Output', use_column_width=True)
        else:
            st.image(image2, caption='Image initiale', use_column_width=True)
            
#############################################################################
#############################################################################
def enhance_image(image,brightness_factor, contrast_factor):
    enhancer = ImageEnhance.Brightness(image)
    brightened_image = enhancer.enhance(brightness_factor)
    enhancer = ImageEnhance.Contrast(brightened_image)
    enhanced_image = enhancer.enhance(contrast_factor)
    return enhanced_image


#############################################################################
#############################################################################
import re
def extract_error_message(error_message_str):
    # Extract error message using regular expression
    match = re.search(r'"message":\s*"([^"]+)"', error_message_str)
    if match:
        return match.group(1)
    else:
        return "Error message not found"
#############################################################################
#############################################################################
def Get_Files(User_ID, storage):
    files = storage.list_files()
    Number = 0
    directory_files = []
    for file in files:
        if file.name.startswith(User_ID+'/Invoices/Annoutated_'):
            #st.write (file.name)
            file_url = storage.child(file.name).get_url(None)
            file_name = os.path.basename(file.name)
            Number += 1
            directory_files.append({'url': file_url, 'name': file_name})
    return directory_files,Number

#############################################################################
#############################################################################
def Get_Data():
    config = {
    'apiKey': "AIzaSyCRX2jKmzxqUWU9W0gpfg9pwGLPDUygUWE",
    'authDomain': "test-b363e.firebaseapp.com",
    'projectId': "test-b363e",
    'storageBucket': "test-b363e.appspot.com",
    'messagingSenderId': "491527659789",
    'databaseURL': "https://test-b363e-default-rtdb.europe-west1.firebasedatabase.app/",
    'appId': "1:491527659789:web:63c58fd431886844129044",
    'measurementId': "G-6RW1Y8B2YJ",
    "serviceAccount": "/teamspace/studios/this_studio/Textra_App/Key.json"
    }
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    auth = firebase.auth()
    storage = firebase.storage()
    return db,auth,storage

#############################################################################
#############################################################################
def Get_Bytes(image):
    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')  # Save the image to the BytesIO object
    return image_bytes.getvalue()


#############################################################################
#############################################################################
def clean_text(text):
    # Apply regex pattern to keep only numbers, dots, and commas
    cleaned_text = re.sub(r"[^0-9.,]+", "", text)
    return cleaned_text

def Get_Json(Dict):
    return json.dumps(Dict, indent=4)

def save_json_to_file(data, file_path):
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    print("JSON file saved successfully.")














