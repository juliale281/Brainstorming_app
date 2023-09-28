# chạy tốt
# cho phép chọn 2 khối-môn, nhiều yccd
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
import json

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
vote_option = ['Sử dụng được hoặc chỉ cần điều chỉnh một ít','Có ý dùng được nhưng cần điều chỉnh nhiều', 'Không sử dụng được','Không liên quan', 'Không hiểu', 'Tương tự ý tưởng phía trước']
st.write('## Chọn yêu cầu cần đạt')

st.write('### Môn học chủ đạo')
khoi1 = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique(),index = 6, key = 'khoi1')
mon1 = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi1].dropna().unique(), index = 1, key = 'mon1')
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi1) & (df_yccd['Môn'] == mon1)]
yccd1 = st.multiselect('Yêu cầu cần đạt',yccd_filter, key = 'yccd1')
try:
    chuDe1 = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd1[0], 'Chủ đề'].iloc[0]
    diemKienThuc1 = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd1[0], 'Điểm kiến thức'].iloc[0]
except IndexError:
    chuDe1 = ''
    diemKienThuc1 = ''
yccd1 = ' và '.join(yccd1)

st.write('### Môn học tích hợp')
khoi2 = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique(),index = 6, key = 'khoi2')
mon2 = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi2].dropna().unique(), index = 1, key = 'mon2')
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi2) & (df_yccd['Môn'] == mon2)]
yccd2 = st.multiselect('Yêu cầu cần đạt',yccd_filter, key = 'yccd2')
try:
    chuDe2 = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd2[0], 'Chủ đề'].iloc[0]
    diemKienThuc2 = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd2[0], 'Điểm kiến thức'].iloc[0]
except IndexError:
    chuDe2 = ''
    diemKienThuc2 = ''
yccd2 = ' và '.join(yccd2)


yccd = ' và '.join([yccd1, yccd2])

khoi = khoi1

# khoi = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique(),index = 6)
# mon = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi].dropna().unique(), index = 1)
# yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi) & (df_yccd['Môn'] == mon)]
# yccd = st.multiselect('Yêu cầu cần đạt',yccd_filter)
# try:
#     chuDe = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd[0], 'Chủ đề'].iloc[0]
#     diemKienThuc = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd[0], 'Điểm kiến thức'].iloc[0]
# except IndexError:
#     chuDe = ''
#     diemKienThuc = ''

# yccd = ' và '.join(yccd)
prompt = f'''
    Bạn hãy bỏ qua những đối thoại phía trước. Tôi muốn bạn đóng vai chuyên gia giáo dục STEM với nhiều ý tưởng thú vị. 
    Tôi sẽ cung cấp cho bạn mục tiêu bài học, bạn hãy gợi ý cho tôi 5 ý tưởng dự án sáng chế một món đồ nào đó để giúp đạt được mục tiêu đó.
    Mục tiêu bài học là : học sinh có thể {yccd}.
    Thời lượng bài học là 70 phút, học sinh đang học lớp {khoi[1]}.
    Không cần nhắc lại câu hỏi, chỉ cần ghi kết quả.''' + '''

    Trình bày câu trả lời theo định dạng json :
    
    {
    
        "yTuong": [
        
            {
            
                "Tên dự án": "...",

                "Mô tả": "..."

            },

            {
            
                "Tên dự án": "...",

                "Mô tả": "..."

            }

            {
            
                "Tên dự án": "...",

                "Mô tả": "..."

            }

            {
            
                "Tên dự án": "...",

                "Mô tả": "..."

            }

            {
            
                "Tên dự án": "...",

                "Mô tả": "..."

            }

        ]

    }

    Ví dụ:

    Hỏi : "Gợi ý cho tôi ý tưởng dự án qua đó học sinh có thể Mô tả được sơ lược cách đo tốc độ bằng đồng hồ bấm giây và cổng quang điện trong dụng cụ thực hành ở nhà trường; thiết bị “bắn tốc độ” trong kiểm tra tốc độ các phương tiện giao thông."

    Trả lời:

    "Tên dự án: Thiết kế và xây dựng máy đo tốc độ xe đạp.

    Mô tả: Học sinh có thể tạo ra một máy đo tốc độ cho xe đạp bằng cách sử dụng đồng hồ bấm giây và cổng quang điện. 
    Học sinh có thể đặt cổng quang điện ở một khoảng cách cố định và sử dụng đồng hồ bấm giây để đo thời gian mà xe đạp mất để đi qua cổng. 
    Từ đó, họ có thể tính toán tốc độ của xe đạp."
    '''

# Hàm này để tách câu trả lời dạng json ra
def split_response_json(res):
    ideas = res['yTuong']
    # Accessing individual contact information
    res_splited = []
    for idea in ideas:
        tenDuAn = idea['Tên dự án']
        moTa = idea['Mô tả']
        duAn = 'Dự án : ' + tenDuAn  + '\n\nMô tả : '+ moTa
        res_splited.append(duAn)
    return res_splited

if 'res_splited' not in st.session_state:
    st.session_state.res_splited =['...(bấm Brainstorm để có ý tưởng)...', '...(bấm Brainstorm để có ý tưởng)...','...(bấm Brainstorm để có ý tưởng)...','...(bấm Brainstorm để có ý tưởng)...','...(bấm Brainstorm để có ý tưởng)...']

def number_to_list(num):
    return [1 if i == num else 0 for i in range(3)]

st.write("### Prompt:")
promptToDisplay = f'''Hãy cho tôi 5 ý tưởng dự án qua đó học sinh có thể "{yccd}"'''
st.write(promptToDisplay)

if st.button('Brainstorm'):
    res = json.loads(get_completion(prompt=prompt))
    st.session_state.res_splited = split_response_json(res)
    st.write(st.session_state.res_splited)


with st.form('Đánh giá'):
    st.write('### Ý tưởng 1:')
    st.write(st.session_state.res_splited[0])
    evaluate1 = st.radio('Đánh giá ý tưởng',vote_option, key = 1, index = 0)
    if vote_option.index(evaluate1) < 3:
        x1 = number_to_list(vote_option.index(evaluate1))
        newRow1 = [khoi, mon1, chuDe1, diemKienThuc1, yccd, st.session_state.res_splited[0]] + x1
    else:
        newRow1 = []

    st.write('### Ý tưởng 2:')
    st.write(st.session_state.res_splited[1])
    evaluate2 = st.radio('Đánh giá ý tưởng',vote_option, key = 2, index = 0)
    if vote_option.index(evaluate2) < 3:
        x2 = number_to_list(vote_option.index(evaluate2))
        newRow2 = [khoi, mon1, chuDe1, diemKienThuc1, yccd, st.session_state.res_splited[1]] + x2
    else:
        newRow2 = []


    st.write('### Ý tưởng 3:')
    st.write(st.session_state.res_splited[2])
    evaluate3 = st.radio('Đánh giá ý tưởng',vote_option, key =3, index = 0)
    if vote_option.index(evaluate3) < 3:
        x3 = number_to_list(vote_option.index(evaluate3))
        newRow3 = [khoi, mon1, chuDe1, diemKienThuc1, yccd, st.session_state.res_splited[2]] + x3
    else:
        newRow3 = []

    st.write('### Ý tưởng 4:')
    st.write(st.session_state.res_splited[3])
    evaluate4 = st.radio('Đánh giá ý tưởng',vote_option, key =4, index = 0)
    if vote_option.index(evaluate4) < 3:
        x4 = number_to_list(vote_option.index(evaluate4))
        newRow4 = [khoi, mon1, chuDe1, diemKienThuc1, yccd, st.session_state.res_splited[3]] + x4
    else:
        newRow4 = []

    st.write('### Ý tưởng 5:')
    st.write(st.session_state.res_splited[4])
    evaluate5 = st.radio('Đánh giá ý tưởng',vote_option, key =5, index = 0)
    if vote_option.index(evaluate5) < 3:
        x5 = number_to_list(vote_option.index(evaluate5))
        newRow5 = [khoi, mon1, chuDe1, diemKienThuc1, yccd, st.session_state.res_splited[4]] + x5
    else:
        newRow5 = []

    submit_idea = st.form_submit_button("Submit")
    if submit_idea:
        wks_ideas.append_row(newRow1)
        wks_ideas.append_row(newRow2)
        wks_ideas.append_row(newRow3)
        wks_ideas.append_row(newRow4)
        wks_ideas.append_row(newRow5)
