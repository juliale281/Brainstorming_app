import streamlit as st
import pandas as pd
import gspread
# import datetime
from google.oauth2.service_account import Credentials
from streamlit_star_rating import st_star_rating
import openai

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
def load_ideas():
    sh = gc.open('K-12') #name of file        
    # wks = sh.worksheet(chinhanh) # lấy data từ sheet của chi nhánh được chọn
    wks_ideas = sh.worksheet('test')
    # rows = wks.get_all_values() # get all values of the sheet
    rows = wks_ideas.get_all_values()
    # df = pd.DataFrame(rows[1:],columns=rows[0]) # save values in a dataframe, using the first row of sheets as the columns of dataframe
    df_ideas = pd.DataFrame(rows[1:],columns=rows[0])
    return df_ideas 

df_ideas = load_ideas() # Call the load_ideas function to load the ideas data into a DataFrame.

@st.cache_resource
def connect_ideas():
    sh = gc.open('K-12') #name of file
    wks_ideas = sh.worksheet('test')
    return wks_ideas
wks_ideas = connect_ideas()

if 'openai_model' not in st.session_state:
    st.session_state['openai_model'] = 'gpt-3.5-turbo'

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

def chat_with_gpt(messages):
    response = openai.ChatCompletion.create(
        model=st.session_state["openai_model"],
        messages=messages,
        temperature=0.8,
    )
    return response.choices[0].message["content"]

openai.api_key = st.secrets["openai_key"]



st.title('Chọn lọc yêu cầu') # Set the title .

# ------------------------------------------------------------------
# biến để lưu số lượng ideas cần show
if 'display_count' not in st.session_state:
    st.session_state['display_count'] = 0

def reset_display_count(): # hàm này cần được gọi khi user search keyword mới
    st.session_state['display_count'] = 3
# ------------------------------------------------------------------
# Create a text input box for entering keywords to search for ideas
keywords = st.text_input('Từ khóa:', value='', help='Vui lòng nhập từ khóa (Khối, Môn, Chủ đề, Điểm kiến thức, Yêu cầu cần đạt)', key='keywords_input',on_change = reset_display_count)

# ------------------------------------------------------------------
# Filter and order the ideas DataFrame based on the entered keywords.
if not keywords:
    ideas_filtered = pd.DataFrame()
else:
    ideas_filtered = df_ideas.loc[(df_ideas['Ý tưởng'].str.contains(keywords, case=False))]
    ideas_filtered = ideas_filtered.sort_values(by='Đánh giá', ascending=False)

# ------------------------------------------------------------------
def update_rating_history(idea, rating):
    cell = wks_ideas.find(idea)  # Find the cell containing the idea in the worksheet
    row = cell.row  # Get the row number of the idea
    rating_history = wks_ideas.cell(row, df_ideas.columns.get_loc('History rating') + 1).value
    if rating_history:
        rating_history += ", " + str(rating)  # Append the new rating to the existing history
    else:
        rating_history = str(rating)  # Create a new history if it doesn't exist
    wks_ideas.update_cell(row, df_ideas.columns.get_loc('History rating') + 1, rating_history)  # Update the "history rating" column    

    rating_values = [int(r) for r in rating_history.split(", ")]
    average_rating = sum(rating_values) / len(rating_values)
    wks_ideas.update_cell(row, df_ideas.columns.get_loc('Đánh giá') + 1, average_rating)  # Update the "rating" column

def input_change():
    st.session_state.history.append(st.session_state.message)
    st.session_state.message = ""


# # Set empty list for comments/ratings
# comments = ['','','','','']
# stars = [0,0,0,0,0]

# Set empty list for comments/ratings
max_ideas = len(df_ideas)
comments = [''] * max_ideas  # Initialize comments list with empty strings
# stars = [0] * max_ideas  # Initialize stars list with zeros for all possible ideas
# ------------------------------------------------------------------
if 'stars' not in st.session_state:
    st.session_state['stars'] = []
# ------------------------------------------------------------------
if 'submit_stars' not in st.session_state:
    st.session_state['submit_stars'] = []
# ------------------------------------------------------------------
def Cal_nb_of_ideas_to_show(k):
    if st.session_state['display_count'] + k < len(ideas_filtered):
        st.session_state['display_count'] += k
    else:
        st.session_state['display_count'] = len(ideas_filtered)

# ------------------------------------------------------------------
# show n ideas
def show_ideas(n):
    i = 1
    for index, row in ideas_filtered.iterrows():
        if i > n:
            break
        st.write('### Ý tưởng ' + str(i))
        st.write('Ý tưởng:', row['Ý tưởng'])
        
        # Display current rating
        st.write('Đánh giá hiện tại:', format(float(row['Đánh giá']), ".1f"))


        # Interaction with Chatbot
        user_input = st.text_input(f'Chat about Idea {i}:', "", key="input", on_change=input_change)


        # Initialize or retrieve conversation history for the current idea
        chat = st.session_state.get(f"idea_{i}_conversation", [])

        if user_input:
            chat.append({"role": "user", "content": user_input})
            chat.append({"role": "system", "content": f"Bạn thắc mắc về: {row['Ý tưởng']}"})
            
            assistant_response = chat_with_gpt(chat)  # Replace with your actual chat_with_gpt function call
            
            # Add assistant response to conversation history
            chat.append({"role": "assistant", "content": assistant_response})
            
            # Update the conversation history in session state
            st.session_state[f"idea_{i}_conversation"] = chat

            # Display chat history
            for message in reversed(chat):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(message["content"])
                elif message["role"] == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(message["content"])

        
        # User star rating input
        if i < len(st.session_state['stars']):
            st.session_state['stars'][i] = st_star_rating('', 5, 0, 20, True, False, False, key='star' + str(i))
        else:
            st.session_state['stars'].append(st_star_rating('', 5, 0, 20, True, False, False, key='star' + str(i)))
        
        # Submit button
        if i < len(st.session_state['submit_stars']):
            if st.session_state['submit_stars'][i]:
                rating = int(st.session_state['stars'][i])
                update_rating_history(row['Ý tưởng'], rating)
                
                # Update DataFrame with new rating and history
                df_ideas.at[index, 'Đánh giá'] = rating
                df_ideas.at[index, 'History rating'] += f", {rating}"
                
                # Update Streamlit session state directly
                st.session_state['stars'][i] = rating
                st.session_state['submit_stars'][i] = False  # Reset the submit state
                
                st.cache_data.clear()
                st.experimental_rerun()  # Rerun the app after clicking "Submit"
            
            st.session_state['submit_stars'][i] = st.button('Submit', key='submit_stars' + str(i))
        else:
            st.session_state['submit_stars'].append(st.button('Submit', key='submit_stars' + str(i)))

        i += 1
 

        
# ------------------------------------------------------------------
# show ideas and show more
show_ideas(st.session_state['display_count'])
btnShowMore = st.button('Show more')

if btnShowMore:
    Cal_nb_of_ideas_to_show(3)
    st.experimental_rerun()
# ------------------------------------------------------------------
# st.write(st.session_state['display_count'])

# st.write(ideas_filtered)

refresh = st.button('Refresh')
if refresh:
    st.cache_data.clear()
