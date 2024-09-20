import subprocess

# Запуск первого скрипта
process1 = subprocess.Popen(['python', 'script1.py'])

# Запуск второго скрипта
process2 = subprocess.Popen(['python', 'script2.py'])

# Ожидание завершения обоих процессов
process1.wait()
process2.wait()

print("Оба скрипта завершили выполнение.")
