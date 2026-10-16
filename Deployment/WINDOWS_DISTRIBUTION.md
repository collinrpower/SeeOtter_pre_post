# Windows distribution build

This builds a portable 64-bit Windows distribution. The build requires passing
frozen dependency/inference tests and startup checks for the application and all
six extra GUI tools before creating release archives. Local build results are
recorded in BUILD-RESULTS.txt in the parent Desktop folder. Testing on a separate
clean Windows computer remains part of release acceptance below.

## Fix the reported ExifRead error

From the repository's Deployment directory in PowerShell:

```powershell
conda activate "SeeOtter(torch-cpu)"
python -m pip install ExifRead
python -c "import sys, exifread; print(sys.executable); print(exifread.__file__)"
```

The old build script changed Conda environments. Installing requirements into
another Python does not install them into that build environment. Installing a
missing module does not repair an existing executable: rebuild it.
ExifRead's distribution name is `ExifRead`; the Python import is `exifread`.

The original requirements.txt contains machine-specific `file:///` URLs and
omits dependencies used by the extra tools. A failed pip run is not evidence
that all requirements were installed. Do not use that file to reproduce a release.

## Build with the existing working environment

### CPU-only portable build

To rebuild with an existing working CPU-only Python 3.9 x64 environment, select
that environment's Python and pass `-CpuOnly`:

```powershell
.\Build-SeeOtter.ps1 -Python "path\to\cpu-environment\python.exe" -CpuOnly
```

This skips the CUDA-wheel requirement while retaining dependency, EXIF-free
survey import, inference, GUI, and release-archive checks. The default build
still requires CUDA-enabled Torch for the GPU + CPU distribution.

### GPU and CPU portable build

Build with CUDA-enabled Torch so the same executable can automatically select
a compatible NVIDIA GPU or fall back to CPU. A CPU-only Torch wheel cannot use
a GPU, regardless of the recipient's installed CUDA tools. This legacy runtime
targets CUDA 11.3; newer GPU architectures may require a newer inference stack.

Create an isolated Python 3.9 x64 environment from the repository root:

```powershell
python -m venv BuildEnvironment
.\BuildEnvironment\Scripts\python.exe -m pip install -r Deployment/requirements-runtime.txt
.\BuildEnvironment\Scripts\python.exe -m pip check
.\BuildEnvironment\Scripts\python.exe Deployment/preflight.py --require-cuda
.\Build-SeeOtter.ps1 -Python "$PWD\BuildEnvironment\Scripts\python.exe"
```

The build rejects CPU-only Torch, tests automatic device selection, and reruns
the frozen inference self-test with CUDA hidden to check CPU fallback. Detection
prints the selected device, Torch version, CUDA runtime, and GPU name. On a GPU
test computer, run `SeeOtter.exe --self-test --require-gpu` to require actual GPU
inference. Users need a compatible NVIDIA driver but no Python or separate CUDA
toolkit. Keep all bundled files together, including the large torch/lib DLLs.
From a fresh PowerShell process in the repository root,
`./Test-Standalone.ps1 -RequireGpu` checks GPU inference, CPU fallback, and all
GUI entry points with development Python/Conda settings removed.

The requirements pin the recorded runtime's direct dependencies; they are not
a complete transitive dependency lock. Save the successful build's `pip freeze`.

Use the environment that can already run SeeOtter from source. The repository
documents Python 3.9 and an older Torch/SAHI/YOLOv5 stack. Its inference code uses
`sahi.model.Yolov5DetectionModel`; upgrading SAHI or Torch indiscriminately can
break that API or model deserialization. The supplemental requirements below
are not a complete, tested dependency lock. Preserve your working inference
versions and resolve any preflight errors before freezing.

```powershell
conda activate "SeeOtter-cuda"
python -m pip freeze > .\environment-before-packaging.txt
python -m pip install -r .\requirements-cuda.txt
python -m pip install -r .\requirements-packaging.txt
python -m pip check
python .\preflight.py --require-cuda
.\build_application.ps1 -Python (Get-Command python).Source
```

The build uses that exact Python, resolves paths relative to the build script,
bundles model weights, image assets, KivyMD data, native GIS dependencies and
the repository's Deployment/yolov5 directory, and runs the executable's self-test.
It keeps a console for diagnostics. Build failures stop the release step.

Post-build staging preserves the sibling .libs folders and their load-order
files used by pandas, Fiona, Pyogrio and other Windows wheels. It also stages
tkinter.ttk for the GIS tool and copies dependency license/notice files.
The spec excludes optional model-export backends that none of these tools use.
See tested-runtime-versions.json for the actual inference/UI versions used here.

After a successful build, save `python -m pip freeze` and, for a Conda build,
`conda list --explicit` with the release records. These record the actual tested
environment; the old requirements.txt does not.

## What users receive

`dist/SeeOtter-3.5.2-windows-x64.zip` contains the entire portable application
folder. Because it exceeds GitHub's 2 GiB asset limit, the release also creates
`.zip.001` / `.zip.002` parts and `Extract-SeeOtter.cmd`. Download both parts and
the helper into one fresh folder, then double-click the helper to verify their
checksums, join the ZIP, and extract it. Allow about 11 GB of free disk space.
For a locally built complete ZIP, use Extract All. Then double-click
SeeOtter.exe. Python and Conda are not required on the recipient's computer.
Keep the entire folder together; copying the executable alone will not work.
Keep surveys outside the application folder so replacing the app preserves data.
Settings and logs live inside this portable folder, so Program Files is unsuitable.

The launcher contains:

| Tool | Included script |
| --- | --- |
| Survey manager | start_see_otter_no_survey.py |
| Preprocessing and GPS correction | SeeOtter_prepro_GUI_non_Waldo_with_GPS_fix.py |
| GPS extraction | Image_GPS_extract.py |
| Copy Waldo images | Copy_Waldo_Images_Into_1_0_folders.py |
| Move Waldo images | Move_Waldo_Images_Into_1_0_folders.py |
| Counts and odd/even split | SeeOtter_post_pro_count_and_split_odd_even.py |
| GIS camera outlines and points | SeeOtter_Project_Processed_Data.py |

All 24 HelperScripts, including calibration helpers, are included as editable
source and available in the advanced menu. Edit select_survey.py and each helper's
input settings before running it. These preserve their original script behavior;
some move images, overwrite surveys or reset validations. Work on copies.
The Waldo copy/move utilities should be run on a fresh input copy, not repeatedly
on a directory already containing their generated Images output.

Postprocessing expects the SeeOtter result CSVs and
`final_metadata_updated_filepath.csv` in the existing survey directory structure.
The GIS exporter consumes the processed CSV. Preserve those paths between steps.

Command-line options:

```powershell
.\SeeOtter.exe --list-tools
.\SeeOtter.exe --tool preprocess
.\SeeOtter.exe --tool postprocess
.\SeeOtter.exe --self-test
```

The build produces a matching source archive, LICENSE, per-file hash manifest
and SHA256 files for both archives. Ship the corresponding source archive with
the binary. Keep the existing repository license and dependency license notices.
No public release or upload is performed by these scripts.

## Release acceptance on a clean Windows computer

1. Extract the complete ZIP into a path containing spaces, with Python and Conda
   absent. Run --self-test, which checks imports, resources, shapefile write/read,
   model loading and the app window's imports. Test with networking disabled too.
2. Open the survey manager, create a small disposable survey, run predictions,
   validate an image, save, restart, and export results.
3. Open each of the six extra tools. Use a small copied image dataset to exercise
   preprocessing/GPS extraction and Waldo copy/move. Use real result CSVs for
   counts/splits and GIS export; inspect resulting CSVs and shapefiles.
4. Configure and exercise each helper intended for your users against disposable
   survey data. Inclusion does not prove the original helper's settings are valid.
5. Record Windows version, environment lock, model hash, test dataset and results.
   Only promote the archive after these checks pass. Sign the executable if you
   have a distribution certificate; this kit does not sign or create an installer.

If an error occurs, run the executable from PowerShell and inspect
Logs/launcher-error.log plus the PyInstaller build warning file. If a module
imports successfully in the build environment but is still absent from the
executable, add its import/hook to the spec and rebuild cleanly. See
[PyInstaller's import troubleshooting](https://pyinstaller.org/en/stable/when-things-go-wrong.html).
