import streamlit as st
import openai
import time
import pandas as pd
import numpy as np
import gspread

df_yccd = pd.read_csv('yccd_v3.csv')

openai.api_key = st.secrets["openai_key"]

#helper from andrew ng
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.8, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

khoi = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique())
mon = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi].dropna().unique())
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi) & (df_yccd['Môn'] == mon)]
yccd = st.selectbox('Yêu cầu cần đạt',yccd_filter)
chuDe = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Chủ đề'].iloc[0]
diemKienThuc = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Điểm kiến thức'].iloc[0]
# chuDe = df_yccd['Chủ đề'][df_yccd['Yêu cầu cần đạt'] == yccd]
# diemKienThuc = df_yccd['Điểm kiến thức'][df_yccd['Yêu cầu cần đạt'] == yccd]

prompt = f'''
Bạn hãy bỏ qua những đối thoại phía trước. Tôi muốn bạn đóng vai chuyên gia giáo dục STEM. 
Gợi ý cho tôi 1 dự án thực tế giao cho học sinh mà qua đó học sinh có thể thực hiện được điều ghi trong dấu <>

<{yccd}>

Trả lời theo ví dụ mẫu : 

Dự án: Làm một khuôn đá

Mô tả dự án: Học sinh có thể sử dụng một số nguyên vật liệu để tạo ra một khuôn đá. 
Sau đó, các em có thể đổ nước vào khuôn và để nó trong tủ đông để làm đá. 
Các em có thể quan sát và giải thích sự thay đổi nhiệt độ và quá trình chuyển đổi từ nước sang đá".

Thời lượng bài học là 70 phút, học sinh đang học lớp {khoi[1]}.

Hãy nghĩ sáng tạo khi trả lời. Không cần nhắc lại câu hỏi, chỉ cần ghi kết quả.
'''

promptToDisplay = f'''Hãy cho tôi ý tưởng dự án qua đó học sinh có thể "{yccd}"'''

st.write("### Prompt:")
st.write(promptToDisplay)

if 'response' not in st.session_state:
    st.session_state.response = 'value'


sa = gspread.service_account(filename='service_account.json')
sh = sa.open('Brainstorm idea') #name of file 
wks = sh.worksheet('idea') #name of sheet


brainstormButton = st.button('Brainstorm')
if brainstormButton:
    st.session_state.response = get_completion(prompt=prompt)
    st.write(st.session_state.response)

with st.form('Evaluate'):
    st.write('## Đánh giá ý tưởng')
    evaluate = st.radio('Ý tưởng này hợp lý và có thể sử dụng trong thực tế',['Chưa có đánh giá', 'Có', 'Không'])
    newRow = [khoi, mon, chuDe, diemKienThuc, yccd, st.session_state.response, evaluate]
    submitButton = st.form_submit_button('Gửi đánh giá')
    if submitButton:
        wks.append_row(newRow)
        st.cache_resource.clear()

        # st.session_state.response = ''


   