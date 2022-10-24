@echo on
echo "***** batch file running" >> F:\Applications\eRezLife\logs\pc_out.log
time /T >> F:\Applications\eRezLife\logs\pc_out.log

whoami 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1
echo "whoami" 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1

e:
echo "e:" 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1
cd F:\Applications\eRezLife
echo "cd" 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1

call C:\ProgramData\Anaconda3\condabin\activate.bat py310 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1
echo "call activate" 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1
rem call conda list 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1

echo "python eRezLife_to_PowerCampus.py" >> F:\Applications\eRezLife\logs\pc_out.log
C:\ProgramData\Anaconda3\envs\py310\python.exe eRezLife_to_PowerCampus.py 1>> F:\Applications\eRezLife\logs\pc_out.log 2>&1

rem pause
time /T >> F:\Applications\eRezLife\logs\pc_out.log
echo "***** batch file exiting" >> F:\Applications\eRezLife\logs\pc_out.log
echo "****************************************************************"
