@echo on
echo "***** batch file running" >> E:\Applications\ResidenceLife\eRezLife\logs\out.log
time /T >> E:\Applications\ResidenceLife\eRezLife\logs\out.log

whoami 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1
echo "whoami" 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1

e:
echo "e:" 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1
cd E:\Applications\ResidenceLife\eRezLife
echo "cd" 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1

set eRezLife_username=paulsmiths

call C:\ProgramData\Anaconda3\condabin\activate.bat E:\Applications\ResidenceLife\eRezLife\envs 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1
echo "call activate" 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1
rem call conda list 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1

echo "python eResLife.py " >> E:\Applications\ResidenceLife\eRezLife\logs\out.log
E:\Applications\ResidenceLife\eRezLife\envs\python.exe eRezLife.py 1>> E:\Applications\ResidenceLife\eRezLife\logs\out.log 2>&1

rem pause
time /T >> E:\Applications\ResidenceLife\eRezLife\logs\out.log
echo "***** batch file exiting" >> E:\Applications\ResidenceLife\eRezLife\logs\out.log
echo "****************************************************************"
