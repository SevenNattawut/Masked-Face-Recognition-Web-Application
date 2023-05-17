# use to change image file names in folder ** NOT INCLUDED IN A FINAL PROGRAM **
import os

# Function to rename multiple files
def main():
    folder = "static/faceImgs/masked/test/3"
    for count, filename in enumerate(os.listdir(folder)):
        dst = f"re {str(count+1)}.jpg"
        src =f"{folder}/{filename}"  # foldername/filename, if .py file is outside folder
        dst =f"{folder}/{dst}"
         
        # rename() function will
        # rename all the files
        os.rename(src, dst)

    for count, filename in enumerate(os.listdir(folder)):
        dst = f"{str(count+71)}.jpg"
        src =f"{folder}/{filename}"  # foldername/filename, if .py file is outside folder
        dst =f"{folder}/{dst}"
         
        # rename() function will
        # rename all the files
        os.rename(src, dst)


# Driver Code
if __name__ == '__main__':
     
    # Calling main() function
    main()