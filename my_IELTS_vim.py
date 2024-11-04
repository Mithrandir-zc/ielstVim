import sys
import os
import shutil

import re
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QLineEdit, QMessageBox, QSplitter
from PySide6.QtCore import Qt,QEvent,QTimer
from PySide6.QtGui import QFont, QKeyEvent, QTextCursor
from PySide6.QtGui import QFontDatabase
import pyttsx3

class Vim(QWidget):
    def __init__(self):
        super().__init__()
        #storage file path
        self.file_opened = False
        self.file_path = ""
        self.mode_flag = "normal"
        #initilize test mode
        self.current_index = 0
        self.test_content = []
        self.current_directory = os.getcwd()

        #initilize UI
        self.initUI()
        self.text_editor.installEventFilter(self)
        self.active_module = 'command_line'              
        self.command_line.setFocus()
        self.update_directory_view()
        # self.to_mode_normal()

    def initUI(self):
        # 设置无边框窗口，但不使用完全透明的背景
        self.setWindowFlags(Qt.FramelessWindowHint)  
        self.setAttribute(Qt.WA_TranslucentBackground)     
        self.showFullScreen()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        splitter = QSplitter(Qt.Vertical)        
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;  /* 手柄透明 */
                height:0;
            }
            QSplitter {
                background-color: rgba(30, 30, 30, 0.8);
                border: none;
            }
        """)
        #setting directory explorer
        self.directory_shower = QLineEdit(self)
        self.directory_shower.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.directory_shower.setPlaceholderText("Enter command here (e.g. ls, cd <dir>, touch <file>, mkdir <folder>, rm <file>, rmdir <folder>)")
        self.directory_shower.setStyleSheet("background-color: rgba(105,53,156,0.7); color: #D4D4D4; border: none; padding: 0 100px 0 100px; margin: 0; height:120px")
        font = QFont('consolas', 28)
        font.setItalic(True)
        self.directory_shower.setFont(font)
        self.directory_shower.setEnabled(False)
        splitter.addWidget(self.directory_shower)
        # 设置文本编辑框
        self.text_editor = QTextEdit(self)
        self.text_editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_editor.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.text_editor.setStyleSheet("background-color: rgba(30, 30, 30, 0.8); color: #D4D4D4; padding: 20px 100px 20px 100px; margin:0; border: none;")  # 深色背景 + 浅色字体
        self.text_editor.setFont(QFont('consolas', 20))
        self.text_editor.textChanged.connect(self.update_user_input)

        splitter.addWidget(self.text_editor)
        # setting command line widget
        self.command_line = QLineEdit(self)
        self.command_line.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.command_line.setPlaceholderText("Enter command here (e.g. ls, cd <dir>, touch <file>, mkdir <folder>, rm <file>, rmdir <folder>)")
        self.command_line.setStyleSheet("background-color:  rgba(29,41,81,0.8); color: #D4D4D4; border: none; padding: 0px 100px 0 100px; margin: 0; height:150px")
        self.command_line.setFont(QFont('consolas',20))
        splitter.addWidget(self.command_line)


        layout.addWidget(splitter)
        self.setLayout(layout)
        
        self.setWindowTitle('ILETSER')
    def eventFilter(self, obj, event):
        if obj == self.text_editor and event.type() == QEvent.KeyPress:
            # Intercept key press events here
            self.handle_text_editor_keys(event)
            return True
        
        return super().eventFilter(obj, event)


    def update_directory_view(self):
        self.current_directory = os.getcwd()
        self.directory_shower.setText(self.current_directory)
        files_and_dirs = os.listdir(self.current_directory)

        directories = sorted([d for d in files_and_dirs if os.path.isdir(os.path.join(self.current_directory, d))])
        files = sorted([f for f in files_and_dirs if os.path.isfile(os.path.join(self.current_directory, f))])
 
        self.text_editor.clear()
        self.text_editor.append(f"Current Directory: {self.current_directory}")

        if directories:
            self.text_editor.append("Directories:")
            self.text_editor.append("\n".join(directories) + "\n")
        
        if files:
            self.text_editor.append("Files:")
            self.text_editor.append("\n".join(files))
        
        self.to_mode_normal()

    def show_error(self, message):
        #show error info
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setText(message)
        error_box.setStyleSheet("background-color: rgba(30, 30, 30, 0.7); color: #D4D4D4; border: none; padding: 0; margin: 0;")
        error_box.setWindowTitle('Error')
        error_box.exec_()    
        
    def execute_command(self):
        command = self.command_line.text().strip()

        if not command:
            return
        command_parts = command.split()
        command_key = command_parts[0]
        if self.file_opened:
            if command_key == 'exit':
                self.file_opened = False
                self.save_content_file()
                self.close()
            elif command_key == 'close':
                self.close_file()
            else:
                self.show_error(f"Unknown command: {command_key}")
        else:
            if command_key == 'ls':
                self.update_directory_view()
            elif command_key == 'cd':
                if len(command_parts) > 1:
                    self.change_directory(command_parts[1])
                else:
                    self.show_error("No directory specified")
            elif command_key == 'touch':
                if len(command_parts) > 1:
                    self.create_file(command_parts[1])
                else:
                    self.show_error("No file name specified")
            elif command_key == 'mkdir':
                if len(command_parts) > 1:
                    self.create_folder(command_parts[1])
                else:
                    self.show_error("No folder name specified")
            elif command_key == 'rm':
                if len(command_parts) > 1:
                    self.delete_file(command_parts[1])
                else:
                    self.show_error("No file name specified")
            
            elif command_key == 'rmdir':
                if len(command_parts) > 1:
                    self.delete_folder(command_parts[1])
                else:
                    self.show_error("No folder name specified")
            
            elif command_key == 'open':
                if len(command_parts) > 1:
                    self.open_file(command_parts[1])
                else:
                    self.show_error("No file name specified")
            
            elif command_key == 'exit':
                sys.exit(0)
            else:
                self.show_error(f"Unknown command: {command_key}")

    
    def change_directory(self, path):
        try:
            _path = os.path.join(self.current_directory,path)
            try:
                if os.path.isdir(_path):
                    os.chdir(path)
                    self.current_directory = os.getcwd()
                    self.update_directory_view()
            except Exception as e:
                self.show_error(f"Failed to change directory {e}")    
        except FileExistsError:
            self.show_error(f"Directory not found {path}")
    
    def create_file(self,file_name):
        try:
            file_path = os.path.join(self.current_directory,file_name)
            open(file_path,'w').close()
            self.update_directory_view()
        except Exception as e:
            self.show_error(f"Failed to create file: {str(e)}")
    
    def create_folder(self,folder_name):
        try:
            folder_name = os.path.join(self.current_directory,folder_name)
            os.makedirs(folder_name)
            self.update_directory_view()
        except Exception as e:
            self.show_error(f"Failed to create folder: {str(e)}")
    def delete_file(self,file_name):
        try:
            file_path = os.path.join(self.current_directory,file_name)
            os.remove(file_path)
            self.update_directory_view()
        except FileExistsError:
            self.show_error(f"File not found: {file_name}")
        except Exception as e:
            self.show_error(f"Failed to delete file: {str(e)}")
    def delete_folder(self, folder_name):
        try:
            folder_path = os.path.join(self.current_directory, folder_name)  # 使用绝对路径
            if os.path.isdir(folder_path):  # 确保目标是文件夹
                shutil.rmtree(folder_path)
                self.update_directory_view()
            else:
                self.show_error(f"Folder not found: {folder_name}")
        except Exception as e:
            self.show_error(f"Failed to delete folder: {str(e)}")

    
    def open_file(self, file_name):
        try:
            self.file_path = os.path.join(self.current_directory, file_name)
            self.load_file_content()
            self.to_mode_normal()
            self.file_opened = True
            self.directory_shower.setText(self.file_path)
        except FileExistsError:
            self.show_error(f"File not found: {file_name}")
        except Exception as e:
            self.show_error(f"Failed to delete file: {str(e)}")

    def close_file(self):
        if self.file_opened==True:
            self.file_opened = False
            self.save_content_file()
            self.update_directory_view()
        else:
            self.show_error(f"Failed to close file")    
    def update_user_input(self):
        self.user_input = self.text_editor.toPlainText().split('\n')

    # In and out of normal mode:
    def to_mode_normal(self):
        self.mode_flag = "normal"
        self.text_editor.setReadOnly(True)
        self.cursor_position = self.text_editor.textCursor().position()
        self.text_editor.clearFocus()
    # In and out of insert mode:
    def to_mode_insert(self):
        self.mode_flag = "insert"
        self.text_editor.setReadOnly(False)
        self.text_editor.setFocus()
    
    def out_mode_insert(self):
        if os.path.isfile(self.file_path):
            self.save_content_file()
    # In and out of test mode:
    def to_mode_test(self):
        self.mode_flag = "test"
        self.current_index = 0
        testContent = re.sub(r'##.*?##', '', self.read_from_file(), flags=re.DOTALL).strip()
        self.test_content = testContent.split('\n')
        
        self.user_input = ""
        self.user_line = []
        self.text_editor.clear()
        self.text_editor.setReadOnly(False)
        self.text_editor.setFocus()
    def out_mode_test(self):
        self.text_editor.clear()
        self.load_file_content()
    # Load and save 
    def read_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path) as file:
                return file.read()
        else:
            print(f"Unexpected error {self.file_path} does not exist")

    def load_file_content(self):
        content = self.read_from_file()
        self.text_editor.setPlainText(content)

    def save_content_file(self):
        text = self.text_editor.toPlainText()
        with open(self.file_path, "w") as file:
            file.write(text)
        print(f"Words have been saved to {self.file_path} file")

    def keyPressEvent(self, event):
        # 根据活动模块决定响应哪个控件
        if self.active_module == 'text_editor':
            self.handle_text_editor_keys(event)
        elif self.active_module == 'command_line':
            self.handle_command_line_keys(event)

    def handle_command_line_keys(self, event):
        key = event.key()
        print(f"in command_line {key}")
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.execute_command()
        elif key == Qt.Key_F3:
            self.active_module = 'text_editor'  # 切换到 text_editor 模块
            self.text_editor.setFocus()
        else:
            self.command_line.keyPressEvent(event)    


    def handle_text_editor_keys(self, event):
        key = event.key()
        if self.mode_flag == "insert":
            if key == Qt.Key_Escape:
                self.out_mode_insert()
                self.to_mode_normal()
            else:
                self.text_editor.keyPressEvent(event)

        elif self.mode_flag == "normal":
            if key == Qt.Key_I:
                self.to_mode_insert()
            if key == Qt.Key_T:
                self.to_mode_test()
            if key == Qt.Key_Q:
                self.close()
            elif key == Qt.Key_F3:
                self.active_module = 'command_line'  # 切换到 command_line 模块
                self.command_line.setFocus()

        elif self.mode_flag == "test":

            if key == Qt.Key_Return or key == Qt.Key_Enter:
                current_text = self.text_editor.toPlainText().replace('\n', '').strip()
                if "Press Enter to exit test mode..." in current_text:
                    self.out_mode_test()
                    self.to_mode_normal()
                else:
                    self.text_editor.keyPressEvent()
            # 检测 Escape，显示比对结果并提示按 Enter 退出
            elif key == Qt.Key_Escape:
                store_content = self.user_input
                self.text_editor.clear()

                self.text_editor.append("Test Result:\n")
                flag = True
                for word1, word2 in zip(self.test_content, store_content):
                    word_processing = re.sub(r'\(.*?\)', '', word1).strip()
                    if word_processing != word2:
                        flag = False
                        self.text_editor.append(f"STD: {word1} YOURS: {word2}\n")

                if flag and len(self.test_content)==len(store_content):
                    self.text_editor.append(f"Congratulations! Full Mark Dictation!")
                # 提示用户按 Enter 退出测试模式
                self.text_editor.append("\nPress Enter to exit test mode...")
            else:

                self.text_editor.keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Vim()
    window.show()
    sys.exit(app.exec_())
