# Environment

The shared environment all benchmarks and simulations run in. Anyone reproducing
the results should be able to match this exactly. Both teammates should fill in
their own machine's section once.

## Agreed baseline

- **OS:** Ubuntu 24.04 LTS (Linux kernel ≥ 6.8). Paper 1 needs real Linux for
  `strace` / `perf` / `setterm`. Recommended setup: VirtualBox / VMware VM, WSL2,
  or a Docker image — pick one and stick to it.
- **Shell:** GNU Bash 5.2+
- **Java:** OpenJDK 21 (LTS) — used by Paper 2.
- **Python:** 3.11+ — used by Paper 3 simulators and by `common/bench.py` /
  `common/plots.py`.
- **C compiler:** gcc 13+ (for Paper 2 pthreads code).
- **Required system tools:** GNU `time` (verbose `-v` support), `perf`,
  `strace`, `top`, `wodim`/`setterm` for some Paper 1 scripts.
- **Python deps:** `numpy`, `matplotlib`, `pyyaml`, `pandas`.

Install bundle (Ubuntu):

```bash
sudo apt update
sudo apt install -y build-essential time linux-tools-common linux-tools-generic \
                    strace bsdmainutils openjdk-21-jdk python3 python3-pip
pip install --user numpy matplotlib pyyaml pandas
```

## Recorded versions

Each teammate runs this block on their machine and pastes the output below:

```bash
uname -a
lsb_release -a 2>/dev/null
bash --version | head -n1
gcc --version | head -n1
java -version 2>&1 | head -n1
python3 --version
/usr/bin/time --version 2>&1 | head -n1
perf --version 2>/dev/null
```

### endri (Part II owner)

```
$ uname -a
Linux Ubuntulabdesktop 6.17.0-19-generic #19~24.04.2-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar  6 22:56:55 UTC 2026 aarch64 aarch64 aarch64 GNU/Linux

$ lsb_release -a 2>/dev/null
Distributor ID: Ubuntu
Description:    Ubuntu 24.04.3 LTS
Release:        24.04
Codename:       noble

$ bash --version | head -n1
GNU bash, version 5.2.21(1)-release (aarch64-unknown-linux-gnu)

$ gcc --version | head -n1
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0

$ java -version 2>&1 | head -n1
openjdk version "21.0.10" 2026-01-20

$ python3 --version
Python 3.12.3

$ /usr/bin/time --version 2>&1 | head -n1
time (GNU Time) UNKNOWN

$ perf --version 2>/dev/null
perf version 6.17.13
```

Architecture: **aarch64 (ARM64)** — Apple Silicon host running an ARM Ubuntu guest in VirtualBox.

Hardware:
- Host CPU: Apple M1 Pro
- vCPUs allocated to VM: 3
- RAM allocated to VM: 4096 MB (4 GB)
- Storage: 25 GB VDI on virtio-scsi controller (backed by host NVMe SSD)
- Display/network: VMSVGA, Intel PRO/1000 MT NAT (not benchmark-relevant)

### hazis (Part I owner)

```
<paste output here>
```

Hardware: CPU model, cores, RAM, storage type.

## Notes

- macOS dev caveat: `/usr/bin/time` is BSD time on macOS and won't support `-v`.
  Install GNU time and point `bench.py` at it:
  `brew install gnu-time && export GTIME_PATH=$(which gtime)`. All actual
  benchmark runs should happen on Linux anyway.
- Performance numbers should be reported per-machine (don't average across
  different hardware). If only one of us runs the final benchmark sweeps,
  record which machine.
- For Paper 2 JVM measurements, do `--reps ≥ 5` and discard the first reading
  (JVM warmup).
