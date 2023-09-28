import streamlit as st
import openai
import time
import pandas as pd
import numpy as np
import gspread

df_yccd = pd.read_csv('yccd_v3.csv')

openai.api_key = st.secrets["openai_key"]

# ------------------------------------------------------------------------
#helper from andrew ng
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.8, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

# ------------------------------------------------------------------------
khoi = st.selectbox('Khối:',df_yccd['Khối'].dropna().unique())
mon = st.selectbox('Môn:',df_yccd['Môn'][df_yccd['Khối'] == khoi].dropna().unique())
yccd_filter = df_yccd['Yêu cầu cần đạt'][(df_yccd['Khối'] == khoi) & (df_yccd['Môn'] == mon)]
yccd = st.selectbox('Yêu cầu cần đạt',yccd_filter)
chuDe = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Chủ đề'].iloc[0]
diemKienThuc = df_yccd.loc[df_yccd['Yêu cầu cần đạt'] == yccd, 'Điểm kiến thức'].iloc[0]

# ------------------------------------------------------------------------
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

# ------------------------------------------------------------------------
sa = gspread.service_account(filename='service_account.json')
sh = sa.open('Brainstorm idea') #name of file 
wks = sh.worksheet('idea2') #name of sheet

# ------------------------------------------------------------------------
def new_row_to_add(idea,evaluate):
    if evaluate == 'Có':
        newRow = [khoi, mon, chuDe, diemKienThuc, yccd, idea, 1, 0, 0]
    elif evaluate == 'Không':
        newRow = [khoi, mon, chuDe, diemKienThuc, yccd, idea, 0, 1, 0]
    else:
        newRow = [khoi, mon, chuDe, diemKienThuc, yccd, idea, 0, 0, 1]
    return newRow

# ------------------------------------------------------------------------
def add_vote_to_wks(idea, evaluate):
    # Find the row where column F equals 'xyz'
    cell_list = wks.findall(idea, in_column=6)  # 6 is the column number for F

    # Increase the value in column G by 1 for each matching row
    for cell in cell_list:
        row_number = cell.row
        
        if evaluate == 'Có':
            g_value = wks.cell(row_number, 7).value  # 7 is the column number for G
            wks.update_cell(row_number, 7, int(g_value) + 1)
        elif evaluate == 'Không':
            h_value = wks.cell(row_number, 8).value  # 8 is the column number for H
            wks.update_cell(row_number, 8, int(h_value) + 1)
        else:
            i_value = wks.cell(row_number, 9).value  # 9 is the column number for I
            wks.update_cell(row_number, 9, int(i_value) + 1)

# ------------------------------------------------------------------------
def get_random_idea_to_vote(yccd):
    # Find the rows where column E equals 'xyz'
    cell_list = wks.findall(yccd, in_column=5)  # 5 is the column number for E

    # Find the row with the maximum sum of columns G, H, and I
    max_row = None
    max_sum = 0
    for cell in cell_list:
        row_number = cell.row
        g_value = int(wks.cell(row_number, 7).value)  # 7 is the column number for G
        h_value = int(wks.cell(row_number, 8).value)  # 8 is the column number for H
        i_value = int(wks.cell(row_number, 9).value)  # 9 is the column number for I
        row_sum = g_value + h_value + i_value
        if row_sum > max_sum:
            max_row = row_number
            max_sum = row_sum

    # Get the value of column F in the row with the maximum sum
    if max_row is not None:
        f_value = wks.cell(max_row, 6).value  # 6 is the column number for F
    
    return f_value

# ------------------------------------------------------------------------
brainstormButton = st.button('Brainstorm')
if brainstormButton:
    st.session_state.response = get_completion(prompt=prompt)
    st.write(st.session_state.response)

# ------------------------------------------------------------------------
with st.form('Evaluate'):
    st.write('## Đánh giá ý tưởng')
    
    st.write('### Ý tưởng 1')
    evaluate1 = st.radio('Ý tưởng này hợp lý và có thể sử dụng trong thực tế',['Chưa có đánh giá', 'Có', 'Không'])    
    newRow = new_row_to_add(st.session_state.response,evaluate1)

    st.write('### Ý tưởng 2')
    evaluate2 = st.radio('Ý tưởng này hợp lý và có thể sử dụng trong thực tế',['Chưa có đánh giá', 'Có', 'Không'])

    submitButton = st.form_submit_button('Gửi đánh giá')
    if submitButton:
        wks.append_row(newRow)



            
        
