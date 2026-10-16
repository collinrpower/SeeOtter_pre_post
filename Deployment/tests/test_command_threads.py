"""Regression coverage for worker commands dispatching graphics-bound state."""
import contextlib
import io
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kivy.clock import Clock
from kivy.graphics import Canvas, Color
from Controller.see_otter_controller_base import SeeOtterControllerBase, SeeOtterState
from Controller.survey_command_controller import SurveyCommandController

class CommandThreadTests(unittest.TestCase):
    def setUp(self):
        self.controller = SeeOtterControllerBase()
        self.stages = []
        self.main_thread = threading.get_ident()
        self.worker_threads = []
        self.observers = []
        self.canvas = Canvas()
        self.controller.survey = SimpleNamespace(
            save=lambda: self.stage('save'), has_unsaved_changes=False)
        self.controller.state = SeeOtterState.SURVEY_LOADED
        self.controller.bind(state=self.observe, snackbar_message=self.observe,
                             program_status_message=self.observe)
        self.commands = SurveyCommandController(self.controller)

    def observe(self, instance, value):
        self.observers.append(threading.get_ident())
        # This is the same type of callback that failed when dispatched by a worker.
        with self.canvas:
            Color(1, 1, 1, 1)

    def stage(self, name):
        self.stages.append(name)
        self.worker_threads.append(threading.get_ident())

    def drain(self):
        for _ in range(8):
            Clock.tick()

    def test_processing_runs_off_main_but_ui_observers_run_on_main(self):
        with patch('Controller.survey_command_controller.pre_processing', side_effect=lambda *a, **k: self.stage('pre')), \
             patch('Controller.survey_command_controller.run_image_detection', side_effect=lambda *a, **k: self.stage('predict')), \
             patch('Controller.survey_command_controller.post_processing', side_effect=lambda *a, **k: self.stage('post')):
            worker = self.commands.run_processing()
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
        self.drain()
        self.assertEqual(self.stages, ['pre', 'predict', 'post', 'save'])
        self.assertTrue(all(ident != self.main_thread for ident in self.worker_threads))
        self.assertTrue(self.observers)
        self.assertEqual(set(self.observers), {self.main_thread})
        self.assertEqual(self.controller.state, SeeOtterState.SURVEY_LOADED)
        self.assertEqual(self.controller.snackbar_message, 'Completed: Run Processing')

    def test_processing_failure_is_reported_and_not_marked_completed(self):
        with contextlib.redirect_stderr(io.StringIO()), \
             patch('Controller.survey_command_controller.pre_processing', side_effect=RuntimeError('fixture failure')):
            worker = self.commands.run_processing()
            worker.join(timeout=5)
        self.drain()
        self.assertEqual(self.stages, [])
        self.assertIn('Error running command (Run Processing): fixture failure', self.controller.snackbar_message)
        self.assertEqual(self.controller.state, SeeOtterState.SURVEY_LOADED)
        self.assertEqual(set(self.observers), {self.main_thread})

    def test_worker_status_and_idle_updates_are_safe(self):
        def update():
            self.controller.set_state(SeeOtterState.PRE_PROCESSING)
            self.controller.set_snackbar_message('Working')
            self.controller.set_program_status_message('Processing')
            self.controller.set_idle_state()
        worker = threading.Thread(target=update)
        worker.start()
        worker.join(timeout=5)
        self.drain()
        self.assertEqual(set(self.observers), {self.main_thread})
        self.assertEqual(self.controller.state, SeeOtterState.SURVEY_LOADED)

    def test_survey_load_is_dispatched_once_without_clock_dt_becoming_flag(self):
        loaded = SimpleNamespace(has_unsaved_changes=False)
        calls = []
        self.controller.bind(survey=lambda *a: calls.append(threading.get_ident()))
        worker = threading.Thread(target=lambda: self.controller.set_survey(loaded, gui_threadsafe=True))
        worker.start()
        worker.join(timeout=5)
        self.drain()
        self.assertIs(self.controller.survey, loaded)
        self.assertEqual(calls, [self.main_thread])

if __name__ == '__main__':
    unittest.main()
