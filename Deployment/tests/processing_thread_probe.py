"""Run inside the frozen runtime to verify processing/UI thread separation."""
import contextlib
import io
import threading
from types import SimpleNamespace
from kivy.clock import Clock
from kivy.graphics import Canvas, Color
from Controller.see_otter_controller_base import SeeOtterControllerBase, SeeOtterState
import Controller.survey_command_controller as command_module

main_thread = threading.get_ident()
controller = SeeOtterControllerBase()
stages, stage_threads, ui_threads = [], [], []
canvas = Canvas()

def stage(name):
    stages.append(name)
    stage_threads.append(threading.get_ident())

def observe(instance, value):
    ui_threads.append(threading.get_ident())
    with canvas:
        Color(1, 1, 1, 1)

def drain():
    for _ in range(8):
        Clock.tick()

controller.survey = SimpleNamespace(save=lambda: stage('save'), has_unsaved_changes=False)
controller.state = SeeOtterState.SURVEY_LOADED
controller.bind(state=observe, snackbar_message=observe, program_status_message=observe)
commands = command_module.SurveyCommandController(controller)
original = (command_module.pre_processing, command_module.run_image_detection, command_module.post_processing)
try:
    command_module.pre_processing = lambda *a, **k: stage('pre')
    command_module.run_image_detection = lambda *a, **k: stage('predict')
    command_module.post_processing = lambda *a, **k: stage('post')
    worker = commands.run_processing()
    worker.join(timeout=5)
    assert not worker.is_alive()
    drain()
    assert stages == ['pre', 'predict', 'post', 'save'], stages
    assert stage_threads and all(ident != main_thread for ident in stage_threads)
    assert ui_threads and set(ui_threads) == {main_thread}, ui_threads
    assert controller.state == SeeOtterState.SURVEY_LOADED
    assert controller.snackbar_message == 'Completed: Run Processing'
    print('PASS: frozen processing runs off main; graphics-bound callbacks run on main')

    def fail(*a, **kw):
        raise RuntimeError('thread regression fixture')
    command_module.pre_processing = fail
    with contextlib.redirect_stderr(io.StringIO()):
        worker = commands.run_processing()
        worker.join(timeout=5)
    drain()
    assert 'Error running command (Run Processing): thread regression fixture' in controller.snackbar_message
    assert controller.state == SeeOtterState.SURVEY_LOADED
    print('PASS: frozen processing errors reach the UI without false completion')
finally:
    (command_module.pre_processing, command_module.run_image_detection,
     command_module.post_processing) = original
