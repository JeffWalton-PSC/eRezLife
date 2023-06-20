@echo on
echo "***** batch file running" >> F:\Applications\eRezLife\logs\out.log
date /T >> F:\Applications\eRezLife\logs\out.log
time /T >> F:\Applications\eRezLife\logs\out.log

whoami 1>> F:\Applications\eRezLife\logs\out.log 2>&1
echo "whoami" 1>> F:\Applications\eRezLife\logs\out.log 2>&1

F:
echo "F:" 1>> F:\Applications\eRezLife\logs\out.log 2>&1
cd F:\Applications\eRezLife
echo "cd" 1>> F:\Applications\eRezLife\logs\out.log 2>&1

set eRezLife_username=paulsmiths

call C:\ProgramData\Anaconda3\condabin\activate.bat py310 1>> F:\Applications\eRezLife\logs\out.log 2>&1
echo "call activate" 1>> F:\Applications\eRezLife\logs\out.log 2>&1
rem call conda list 1>> F:\Applications\eRezLife\logs\out.log 2>&1

echo "python eResLife.py " >> F:\Applications\eRezLife\logs\out.log
C:\ProgramData\Anaconda3\envs\py310\python.exe eRezLife.py 1>> F:\Applications\eRezLife\logs\out.log 2>&1

rem pause
time /T >> F:\Applications\eRezLife\logs\out.log
echo "***** batch file exiting" >> F:\Applications\eRezLife\logs\out.log
echo "****************************************************************" >> F:\Applications\eRezLife\logs\out.log
