import subprocess

# Запуск первого скрипта
process1 = subprocess.Popen(['python', 'epay.py'])

# Запуск второго скрипта
process2 = subprocess.Popen(['python', 'cashin.py'])

# Ожидание завершения обоих процессов
process1.wait()
process2.wait()

print("Оба скрипта завершили выполнение.")
