import streamlit as st
from tensorflow import keras
from tensorflow.keras import backend as K
from PIL import Image
import numpy as np
import cv2

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1' 

import tensorflow as tf


st.title("تشخیص جعلی بودن امضا")
st.title("         ")


uploaded_file_1 = st.file_uploader(
    "تصویر امضا اول وارد کنید", type=["jpg", "png", "jpeg"], key=1
)
uploaded_file_2 = st.file_uploader(
    "تصویر امضا دوم وارد کنید", type=["jpg", "png", "jpeg"], key=2
)


if uploaded_file_1 is not None and uploaded_file_2 is not None:
    img1 = Image.open(uploaded_file_1)
    image_1 = img1.convert("RGB")
    image_1 = np.array(image_1)
    image_1 = cv2.resize(image_1, (100, 100), interpolation=cv2.INTER_LINEAR)
    image_1 = cv2.cvtColor(image_1, cv2.COLOR_BGR2GRAY)
    image_1 = np.expand_dims(image_1, axis=0)
    image_1 = image_1 / 255.0

    img2 = Image.open(uploaded_file_2)
    image_2 = img2.convert("RGB")
    image_2 = np.array(image_2)
    image_2 = cv2.resize(image_2, (100, 100), interpolation=cv2.INTER_LINEAR)
    image_2 = cv2.cvtColor(image_2, cv2.COLOR_BGR2GRAY)
    image_2 = np.expand_dims(image_2, axis=0)
    image_2 = image_2 / 255.0

    col1, col2 = st.columns(2)
    with col1:
        st.image(img1, caption="one", use_column_width=True)
    with col2:
        st.image(img2, caption="two", use_column_width=True)

    model = keras.models.load_model("/Users/najmeh/Desktop/projects/model_test.h5")
    y_pred = model.predict([image_1, image_2])
    y_pred = np.argmax(y_pred)
    if y_pred == 1:
        st.write("جعلی")
    else:
        st.write("اصلی")
