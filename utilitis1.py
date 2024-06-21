import ollama
import time 
import numpy as np
from paddleocr import PaddleOCR
import json

def Paddle():
    ocr = PaddleOCR(use_angle_cls=False,lang='fr',rec=False,use_gpu =True)
    return ocr

def Run_ocr(image):
    image_array = np.array(image)
    ocr = Paddle()
    results = ocr.ocr(image_array,  cls=False,rec = True)
    Text = " "
    for i in range(len(results[0])):
        Text+=results[0][i][1][0]+" "   
    return Text

def Run_llama3_Custom(image):
    start_time = time.time()

    Raw_text = Run_ocr(image)
    response = ollama.chat(model='llama_2', messages=[
        {
            'role': 'user',
            'content': f'give just the json file containing main infos from this: {Raw_text}',
        },
    ])

    end_time = time.time()  
    execution_time = end_time - start_time
    Results = To_Dict(response['message']['content'])
    return Results,execution_time,Raw_text

def interact_with_model(user_input):
    response = ollama.chat(model='llama_2', messages=[
        {
            'role': 'user',
            'content': user_input,
        },
    ])
    return response['message']['content']

def To_Dict(Output):
    start_index = Output.find("{")
    end_index = Output.rfind("}") + 1
    json_str = Output[start_index:end_index]
    return json.loads(json_str)