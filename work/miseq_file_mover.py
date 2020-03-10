import os
import subprocess

usb_drive = "/Volumes/BIOFAB external HD"
fastq_dir = "Data/Intensities/BaseCalls"
globus_dir = "/Users/devin/Globus Endpoint"

system = "data-sd2e-projects.sd2e-project-11"

remote_plan_folder = "Plan_37609"
local_run_folder = "200131_M00777_0106_000000000-CT4JP"

local_path = os.path.join(usb_drive, local_run_folder, fastq_dir)
# local_path = globus_dir
remote_path = os.path.join(remote_plan_folder, "ngs_data")


filenames = [
    "442761-Yakov-ligand-Tryp-750_S10_L001_I1_001.fastq.gz"
]

for filename in filenames:
    local_file = os.path.join(local_path, filename)

    cmd = ['files-upload', '-S', system, '-F', local_file, remote_path]
    print(' '.join(cmd))
    print(local_file)
    msg = subprocess.check_output(cmd)
    print(msg)
    print()
