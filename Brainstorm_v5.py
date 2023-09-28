# done, có thể còn bug do star rating không reset mỗi khi sumbit
# cho phép chọn 1 khối-môn, nhiều yccd, chỉ đánh giá 1 tiêu chí và cho phép người dùng thêm comment
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
import streamlit  as st
from streamlit_star_rating import st_star_rating

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
    wks_yccd = sh.worksheet('yccd')
    rows = wks_yccd.get_all_values()
    df_yccd = pd.DataFrame(rows[1:],columns=rows[0])
    return df_yccd
df_yccd= load_yccd()

@st.cache_resource
def connect_ideas():
    sh = gc.open('K-12') #name of file
    wks_ideas = sh.worksheet('test')
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
vote_option = ['Sử dụng được hoặc chỉ cần điều chỉnh một ít','Có ý dùng được nhưng cần điều chỉnh nhiều','Sử dụng được nhưng cần tích hợp với môn khác', 'Không sử dụng được','Không liên quan đến yêu cầu cần đạt', 'Không hiểu', 'Tương tự ý tưởng phía trước']
st.write('## Chọn yêu cầu cần đạt')

khoi = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique(),index = 6)
mon = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi].dropna().unique(), index = 1)
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi) & (df_yccd['Môn'] == mon)]
yccd = st.multiselect('Yêu cầu cần đạt',yccd_filter)
try:
    chuDe = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd[0], 'Chủ đề'].iloc[0]
    diemKienThuc = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd[0], 'Điểm kiến thức'].iloc[0]
except IndexError:
    chuDe = ''
    diemKienThuc = ''

yccd = ' và '.join(yccd)

prompt = f'''
    Bạn hãy bỏ qua những đối thoại phía trước. Tôi muốn bạn đóng vai chuyên gia giáo dục STEM với nhiều ý tưởng thú vị. 
    Tôi sẽ cung cấp cho bạn mục tiêu bài học, bạn hãy gợi ý cho tôi 5 ý tưởng dự án sáng chế một món đồ nào đó để giúp đạt được mục tiêu đó.
    Mục tiêu bài học là : học sinh có thể {yccd}
    Dự án này có độ khó phù hợp với học sinh {int(khoi[1]) + 5} tuổi.
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

# st.write(prompt)
# Hàm này để tách câu trả lời dạng json ra
def split_response_json(res):
    ideas = res['yTuong']
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
    return [1 if i == num else 0 for i in range(4)]

st.write("### Prompt:")
promptToDisplay = f'''Hãy cho tôi 5 ý tưởng dự án qua đó học sinh có thể "{yccd}"'''
st.write(promptToDisplay)


if st.button('Brainstorm'):
    res = json.loads(get_completion(prompt=prompt))
    st.session_state.res_splited = split_response_json(res)
    # st.write(st.session_state.res_splited)

for i in range(5):
    if "temp_comment"+str(i) not in st.session_state:
        st.session_state["temp_comment"+str(i)] = ''
    if "temp_star"+str(i) not in st.session_state:
        st.session_state["temp_star"+str(i)] = 0
    if 'star'+str(i) not in st.session_state:
        st.session_state['star'+str(i)] = 0


def clear_comment():
    for i in range(5):
        st.session_state["temp_comment"+str(i)] = st.session_state["comment" + str(i)]
        st.session_state["comment" + str(i)] = ''

        st.session_state["temp_star"+str(i)] = st.session_state["star"+str(i)]
        st.session_state["star"+str(i)] = 0
    
comments = ['','','','','']
stars = [0,0,0,0,0]

with st.form('Đánh giá'):
    st.write('''#### Đánh giá ý tưởng trên thang 1 đến 5, trong đó:
             \n1 - Không khả thi
             \n2 - Khả thi nhưng quen thuộc quá rồi
             \n3 - Khả thi và cũng có chút sáng tạo
             \n4 - Khả thi và sáng tạo
             \n5 - Khả thi và wow! rất sáng tạo luôn, cũng rất thực tế nữa
             ''')
    for i in range(5):
        st.write('### Ý tưởng ' + str(i + 1) + ' :')
        st.write(st.session_state.res_splited[i])

        stars[i] = st_star_rating('', 5, 0, 20, True, False, False, key = 'star'+str(i))
        comments[i] = st.text_input('Nhận xét:' ,value='', key = 'comment'+str(i))

    submit_idea = st.form_submit_button("Submit", on_click = clear_comment)
    if submit_idea:
        for i in range(5):
            newRow = [khoi, mon, chuDe, diemKienThuc, yccd, st.session_state.res_splited[i], st.session_state['temp_star'+str(i)], st.session_state["temp_comment"+str(i)]]
            wks_ideas.append_row(newRow)
