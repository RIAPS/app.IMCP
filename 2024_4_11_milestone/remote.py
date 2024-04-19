# from fabric2 import ThreadingGroup as Group
from fabric2 import SerialGroup as Group
import os
import pathlib
import tarfile
import time

mask = "192.168.10"
nodes = [f"{mask}.{x}" for x in [111, 112]]  # , 115, 116]]

pool = Group(*nodes)

pool.run("hostname")
pool.run("mkdir -p ~/UC3_SET_OP_PNTS/scripts")
top = pathlib.Path(__file__).absolute().parents[1]
pool.put(f"{top}/2024_4_11_milestone/set_op.py", "/home/riaps/UC3_SET_OP_PNTS/scripts")
pool.put(
    f"{top}/2024_4_11_milestone/output.yaml", "/home/riaps/UC3_SET_OP_PNTS/scripts"
)
pool.put(f"{top}/2024_4_11_milestone/api.py", "/home/riaps/UC3_SET_OP_PNTS/scripts")


# Step 1: Create a tarball of the directory
cfgs = top / "cfg_ncsu"
with tarfile.open("cfgs.tar.gz", "w:gz") as tar:
    tar.add(cfgs, arcname="cfg_ncsu")

# Step 2: Transfer the tarball to the remote server
pool.put("cfgs.tar.gz", "/home/riaps/UC3_SET_OP_PNTS/cfgs.tar.gz")

# Step 3: Extract the tarball on the remote server
pool.run(
    "tar -xzf /home/riaps/UC3_SET_OP_PNTS/cfgs.tar.gz -C /home/riaps/UC3_SET_OP_PNTS"
)
pool.run("rm /home/riaps/UC3_SET_OP_PNTS/cfgs.tar.gz")

pool.run("ls ~/UC3_SET_OP_PNTS")

# pool.run("python3 ~/UC3_SET_OP_PNTS/set_op.py")
