#!/usr/bin/python3
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
# Developed by: Nasel(http://www.nasel.com.ar)
#
# Authors:
# Matías Fontanini
# Santiago Alessandri
# Gastón Traberg

from threading import Thread, Event, Lock
from exceptions import *

class Threader:
    def __init__(self, max_threads):
        self.threads = []
        self.events = []
        self.results = []
        self.tasks = []
        self.running = True
        self.task_end_lock = Lock()
        self.finish_event = Event()
        for i in range(max_threads):
            self.events.append(Event())
            self.threads.append(Thread(target=self.thread_proc, kwargs={'index':i}))
            self.tasks.append(None)
            self.results.append(None)
            self.threads[i].start()

    def stop(self):
        self.running = False
        for event in self.events:
            event.set()
        self.finish_event.set()

    def thread_proc(self, index):
        while self.running:
            self.events[index].wait()
            self.events[index].clear()
            if not self.running or self.tasks[index] is None:
                return
            start, count, nthreads, functor = self.tasks[index]
            data = []
            try:
                for i in range(start, start + count):
                    result = functor(i)
                    if result is None:
                        break
                    data.append(result)
            except (ConnectionException, QueryError):
                pass
            except Exception as ex:
                import traceback, sys
                traceback.print_exc(file=sys.stdout)
            self.results[index] = data
            self.task_end_lock.acquire()
            self.finished = self.finished + 1
            if self.finished == nthreads:
                self.finish_event.set()
            self.task_end_lock.release()

    def execute(self, count, functor):
        if count < len(self.threads):
            nthreads = count
            per_thread = 1
            extra = 0
        else:
            per_thread = count // len(self.threads)
            nthreads = len(self.threads)
            extra = count % len(self.threads)
        self.finished = 0
        start = 0
        self.finish_event.clear()
        for i in range(nthreads):
            this_thread = per_thread
            if extra > 0:
                this_thread += 1
                extra -= 1
            self.tasks[i] = (start, this_thread, nthreads, functor)
            self.events[i].set()
            start += this_thread
        self.finish_event.wait()
        if self.finished != nthreads:
            return []
        output = []
        for i in range(nthreads):
            output += self.results[i]
        return output
