###############################################################################################################################
#Import library
###############################################################################################################################
import streamlit as st
import pandas as pd
import gspread
# import datetime
import numpy as np
from google.oauth2.service_account import Credentials
import openai


###############################################################################################################################
# kết nối file yêu cầu cần đạt
###############################################################################################################################
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# Create a connection object.
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes = scopes
)
gc = gspread.authorize(credentials)

@st.cache_data #cache data diem danh de khong can load lai
def load_yccd():
    sh = gc.open('K-12') #name of file        
    # wks = sh.worksheet(chinhanh) # lấy data từ sheet của chi nhánh được chọn
    wks_yccd = sh.worksheet('yccd')
    # rows = wks.get_all_values() #get all values of the sheet
    rows = wks_yccd.get_all_values()
    # df = pd.DataFrame(rows[1:],columns=rows[0]) # save values in a dataframe, using the first row of sheets as the columns of dataframe
    df_yccd = pd.DataFrame(rows[1:],columns=rows[0])
    return df_yccd
df_yccd= load_yccd()
# # st.write(df_yccd)

@st.cache_resource
def connect_ideas():
    sh = gc.open('K-12') #name of file
    wks_ideas = sh.worksheet('ideas')
    return wks_ideas
wks_ideas = connect_ideas()
###############################################################################################################################
# helper from andrew ng
###############################################################################################################################
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.8, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

openai.api_key = st.secrets["openai_key"]

###############################################################################################################################
# chọn yccđ
###############################################################################################################################
st.write('## Chọn yêu cầu cần đạt')
khoi = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique(),index = 6)
mon = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi].dropna().unique(), index = 1)
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi) & (df_yccd['Môn'] == mon)]
yccd = st.selectbox('Yêu cầu cần đạt',yccd_filter)
chuDe = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Chủ đề'].iloc[0]
diemKienThuc = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Điểm kiến thức'].iloc[0]
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

st.write("### Prompt:")
promptToDisplay = f'''Hãy cho tôi 3 ý tưởng dự án qua đó học sinh có thể "{yccd}"'''
st.write(promptToDisplay)

if 'response1' not in st.session_state:
    st.session_state.response1 = '...(bấm Brainstorm để có ý tưởng)...'
if 'response2' not in st.session_state:
    st.session_state.response2 = '...(bấm Brainstorm để có ý tưởng)...'
if 'response3' not in st.session_state:
    st.session_state.response3 = '...(bấm Brainstorm để có ý tưởng)...'

if st.button('Brainstorm'):
    st.session_state.response1 = get_completion(prompt=prompt)
    st.session_state.response2 = get_completion(prompt=prompt)
    st.session_state.response3 = get_completion(prompt=prompt)

with st.form('Đánh giá'):
    st.write('### Ý tưởng 1:')
    st.write(st.session_state.response1)
    evaluate1 = st.radio('Đánh giá ý tưởng',['Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được', 'Không sử dụng được','Chưa có đánh giá'], key = 1, index = 2)
    if evaluate1 == 'Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được':
        x1 = [1,0,0]
    elif evaluate1 == 'Không sử dụng được':
        x1 = [0,1,0]
    else:
        x1 = [0,0,1]

    st.write('### Ý tưởng 2:')
    st.write(st.session_state.response2)
    evaluate2 = st.radio('Đánh giá ý tưởng',['Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được', 'Không sử dụng được', 'Chưa có đánh giá'], key = 2, index = 2)
    if evaluate2 == 'Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được':
        x2 = [1,0,0]
    elif evaluate2 == 'Không sử dụng được':
        x2 = [0,1,0]
    else:
        x2 = [0,0,1]


    st.write('### Ý tưởng 3:')
    st.write(st.session_state.response3)
    evaluate3 = st.radio('Đánh giá ý tưởng',['Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được', 'Không sử dụng được', 'Chưa có đánh giá'], key =3, index = 2)
    if evaluate3 == 'Sử dụng được hoặc điều chỉnh một ít sẽ sử dụng được':
        x3 = [1,0,0]
    elif evaluate3 == 'Không sử dụng được':
        x3 = [0,1,0]
    else:
        x3 = [0,0,1]
    
    newRow1 = [khoi, mon, chuDe, diemKienThuc, yccd, st.session_state.response1] + x1
    newRow2 = [khoi, mon, chuDe, diemKienThuc, yccd, st.session_state.response2] + x2
    newRow3 = [khoi, mon, chuDe, diemKienThuc, yccd, st.session_state.response3] + x3

    submit_idea = st.form_submit_button("Submit")
    if submit_idea:
        wks_ideas.append_row(newRow1)
        wks_ideas.append_row(newRow2)
        wks_ideas.append_row(newRow3)
