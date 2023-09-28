import pandas as pd
import csv

# read the CSV file into a dataframe
df_yccd = pd.read_csv('yccd.csv')
df_yccd = df_yccd.fillna('empty')
# 'Khối', 'Môn', 'Chủ đề', 'Điểm kiến thức', 'Yêu cầu cần đạt', 'Ghi chú'
# display the first 5 rows of the dataframe
# print(df_yccd.head())
print(df_yccd.columns)

newList = []

for i in range(len(df_yccd)):
    # print(i)
    # print(df_yccd['Yêu cầu cần đạt'][i])
    splitRow = df_yccd['Yêu cầu cần đạt'][i].split("\n")
    newSplitRow = []
    for yccd in splitRow:
        # print(yccd)
        if yccd[0] == "-":
            newSplitRow.append(yccd[2:])
        else:
            if len(newSplitRow) > 0:
                newSplitRow[-1] += (" "+ yccd)
            else:
                newSplitRow.append(yccd)

    for yccd in newSplitRow:
        newRow = [df_yccd['Khối'][i],df_yccd['Môn'][i],df_yccd['Chủ đề'][i],df_yccd['Điểm kiến thức'][i],yccd,df_yccd['Ghi chú'][i]]
        newList.append(newRow)
    # print(splitRow)
# print(newList[100])

print(len(newList),len(newList[0]))




with open('new_yccd.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(newList)

