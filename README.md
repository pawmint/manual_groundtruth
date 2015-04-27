# Manual groundtruth

Manually labelling our dataset with our observations.

Observations will be saved in a csv file, with the following informations:

* Resident
* Start time
* End time
* Type_of_observation (`system failure`, `sensing error`, `reasoning error`, `correct inference`, `other`)
* Confidence (5 levels: `just a doubt`, `perhaps`, `probably`, `very likely`, and `sure`)
* Guessed activity
* Remarks

## Getting started

```bash
$ pip install git+ssh://git@github.com/pawmint/manual_groundtruth.git

$ manual-gt <my_csv_file.csv>
```

Then, just follow the guide ;).
