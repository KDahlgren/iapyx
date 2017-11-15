
# Iapyx

A stand-alone translator for Dedalus programs.

# Installation

```
python setup.py
```

# Adding New Rewrite Methods
Iapyx allows the easy integration of new rewriting methods into the translation workflow. Currently, the design modularizes the several currently available necessary and optional rewriting processes and reduces program rewrites to appropriate API calls within the 'rewrite(...)' method located in the 'src/dedt/dedt.py' file. Observe different orderings of rewrite calls may affect the final ouptut program. Adding new rewriting methods into the workflow is as simple as coding-up the rewriting logic somewhere in the repo (preferably NOT in src/dedt/) and adding the API call(s) to the dedt.py 'rewrite' method.
<br><br>
Alternatively, developers can experiment with new rewriting methods outside of the larger iapyx workflow by integrating calls to the experimental modules into the appropriate locations of the 'dedalus_to_datalog' method in the 'src/drivers/iapyx_concise.py' file. Please refer to the in-line documentation in iapyx_concise.py for further guidance.

# Using the Concise driver
Iapyx also includes a concise driver which condences the primary steps of the complete workflow into a single file.<br>
Use commands aligning with the following format to interact with the concise driver :
```
cd src/drivers/
python iapyx_concise.py foo.ded
```
Observe "foo.ded" is an input dedalus program. The driver will output the translated c4 program to standard out.

# QA
Run the quality assurance tests to make sure the iapyx workflow works on your system.
<br>
To run tests in bulk, use the following command sequence :
```
cd qa/
python unittests_driver.py
```
To run tests individually, use commands of the format :
```
python -m unittest Test_dedt.Test_dedt.test_example7
```

# Examples
Run examples to test whether c4 installed successfully. COMING SOON : c4-specific unit tests =]
```
cd examples/omissionProblem/
bash run_0.sh
```
If the execution doesn't puke, you're good to go! <br>
P.S. : you can ignore these messages if they pop up:
```
rm: ./IR.db: No such file or directory
rm: ./tmp.txt: No such file or directory
```
