from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple


# ========= TEACHERS =========

@dataclass
class Teacher(ABC):
    name: str

    @property
    @abstractmethod
    def can_give_lecture(self) -> bool:
        ...

    @property
    @abstractmethod
    def can_lead_practical(self) -> bool:
        ...

    @property
    @abstractmethod
    def can_supervise_coursework(self) -> bool:
        ...


@dataclass
class Lecturer(Teacher):
    @property
    def can_give_lecture(self) -> bool:
        return True

    @property
    def can_lead_practical(self) -> bool:
        return False

    @property
    def can_supervise_coursework(self) -> bool:
        return True


@dataclass
class Assistant(Teacher):
    @property
    def can_give_lecture(self) -> bool:
        return False

    @property
    def can_lead_practical(self) -> bool:
        return True

    @property
    def can_supervise_coursework(self) -> bool:
        return True


@dataclass
class ExternalMentor(Teacher):
    @property
    def can_give_lecture(self) -> bool:
        return False

    @property
    def can_lead_practical(self) -> bool:
        return False

    @property
    def can_supervise_coursework(self) -> bool:
        return True


# ========= SESSIONS + FACTORY METHOD =========

@dataclass
class ClassSession(ABC):
    time: str
    room: str
    teacher: Teacher
    course_name: str

    @abstractmethod
    def kind(self) -> str:
        ...

    @abstractmethod
    def _check_teacher_role(self) -> None:
        ...

    def __post_init__(self) -> None:
        self._check_teacher_role()


@dataclass
class LectureSession(ClassSession):
    def kind(self) -> str:
        return "lecture"

    def _check_teacher_role(self) -> None:
        if not self.teacher.can_give_lecture:
            raise ValueError(f"{self.teacher.name} cannot give lectures")


@dataclass
class PracticalSession(ClassSession):
    def kind(self) -> str:
        return "practical"

    def _check_teacher_role(self) -> None:
        if not self.teacher.can_lead_practical:
            raise ValueError(f"{self.teacher.name} cannot lead practicals")


class SessionFactory(ABC):
    @abstractmethod
    def create_session(
        self,
        time: str,
        room: str,
        teacher: Teacher,
        course_name: str,
    ) -> ClassSession:
        ...


class LectureFactory(SessionFactory):
    def create_session(
        self,
        time: str,
        room: str,
        teacher: Teacher,
        course_name: str,
    ) -> ClassSession:
        return LectureSession(time=time, room=room, teacher=teacher, course_name=course_name)


class PracticalFactory(SessionFactory):
    def create_session(
        self,
        time: str,
        room: str,
        teacher: Teacher,
        course_name: str,
    ) -> ClassSession:
        return PracticalSession(time=time, room=room, teacher=teacher, course_name=course_name)


# ========= COURSEWORK =========

@dataclass
class CourseWork(ABC):
    course_name: str
    title: str
    supervisor: Teacher

    @abstractmethod
    def submission_type(self) -> str:
        ...

    @abstractmethod
    def submit(self, data: str) -> str:
        ...


@dataclass
class OnlineSubmissionWork(CourseWork):
    def submission_type(self) -> str:
        return "online"

    def submit(self, data: str) -> str:
        return f"{self.course_name}: file '{data}' uploaded via LMS"


@dataclass
class GitHubSubmissionWork(CourseWork):
    def submission_type(self) -> str:
        return "github"

    def submit(self, data: str) -> str:
        return f"{self.course_name}: repo '{data}' linked on GitHub"


@dataclass
class OralDefenseWork(CourseWork):
    def submission_type(self) -> str:
        return "oral"

    def submit(self, data: str) -> str:
        return f"{self.course_name}: oral defense scheduled at {data}"


# ========= ABSTRACT FACTORY =========

class CourseFactory(ABC):
    def __init__(self, course_name: str):
        self.course_name = course_name

    @abstractmethod
    def create_lecture(
        self,
        time: str,
        room: str,
        teacher: Teacher,
    ) -> LectureSession:
        ...

    @abstractmethod
    def create_practical(
        self,
        time: str,
        room: str,
        teacher: Teacher,
    ) -> PracticalSession:
        ...

    @abstractmethod
    def create_coursework(self, supervisor: Teacher) -> CourseWork:
        ...


class ProgrammingCourseFactory(CourseFactory):
    def __init__(self):
        super().__init__("Programming")

    def create_lecture(self, time: str, room: str, teacher: Teacher) -> LectureSession:
        return LectureSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_practical(self, time: str, room: str, teacher: Teacher) -> PracticalSession:
        return PracticalSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_coursework(self, supervisor: Teacher) -> CourseWork:
        return GitHubSubmissionWork(
            course_name=self.course_name,
            title="Final Programming Project",
            supervisor=supervisor,
        )


class DatabasesCourseFactory(CourseFactory):
    def __init__(self):
        super().__init__("Databases")

    def create_lecture(self, time: str, room: str, teacher: Teacher) -> LectureSession:
        return LectureSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_practical(self, time: str, room: str, teacher: Teacher) -> PracticalSession:
        return PracticalSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_coursework(self, supervisor: Teacher) -> CourseWork:
        return OnlineSubmissionWork(
            course_name=self.course_name,
            title="Database Design Report",
            supervisor=supervisor,
        )


class MathCourseFactory(CourseFactory):
    def __init__(self):
        super().__init__("Discrete Math")

    def create_lecture(self, time: str, room: str, teacher: Teacher) -> LectureSession:
        return LectureSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_practical(self, time: str, room: str, teacher: Teacher) -> PracticalSession:
        return PracticalSession(time=time, room=room, teacher=teacher, course_name=self.course_name)

    def create_coursework(self, supervisor: Teacher) -> CourseWork:
        return OralDefenseWork(
            course_name=self.course_name,
            title="Combinatorics Oral Exam",
            supervisor=supervisor,
        )


# ========= STUDENT GROUP =========

@dataclass
class StudentGroup:
    name: str
    students: List[str]
    sessions: List[ClassSession]

    def add_session(self, session: ClassSession) -> None:
        self.sessions.append(session)

    def enroll_in_course(
        self,
        factory: CourseFactory,
        lecture_time: str,
        lecture_room: str,
        lecture_teacher: Teacher,
        practical_time: str,
        practical_room: str,
        practical_teacher: Teacher,
        supervisor: Teacher,
    ) -> CourseWork:
        lecture = factory.create_lecture(lecture_time, lecture_room, lecture_teacher)
        practical = factory.create_practical(practical_time, practical_room, practical_teacher)
        self.add_session(lecture)
        self.add_session(practical)
        return factory.create_coursework(supervisor)

    def check_conflicts(self) -> List[Tuple[ClassSession, ClassSession]]:
        conflicts: List[Tuple[ClassSession, ClassSession]] = []
        for i in range(len(self.sessions)):
            for j in range(i + 1, len(self.sessions)):
                a = self.sessions[i]
                b = self.sessions[j]
                if a.time == b.time:
                    conflicts.append((a, b))
        return conflicts


# ========= DEMO SCRIPT =========

def main() -> None:
    lecturer_prog = Lecturer("Dr. Programming")
    lecturer_db = Lecturer("Dr. Databases")
    lecturer_math = Lecturer("Dr. Math")

    assistant_prog = Assistant("Asst. Prog")
    assistant_db = Assistant("Asst. DB")
    assistant_math = Assistant("Asst. Math")

    mentor_industry = ExternalMentor("Industry Mentor")

    prog_factory = ProgrammingCourseFactory()
    db_factory = DatabasesCourseFactory()
    math_factory = MathCourseFactory()

    group_fep21 = StudentGroup("FeP-21", ["Alice", "Bob"], [])
    group_fep22 = StudentGroup("FeP-22", ["Charlie", "Dana"], [])

    cw_prog = group_fep21.enroll_in_course(
        prog_factory,
        lecture_time="Mon 10:00",
        lecture_room="101",
        lecture_teacher=lecturer_prog,
        practical_time="Wed 12:00",
        practical_room="Lab A",
        practical_teacher=assistant_prog,
        supervisor=mentor_industry,
    )

    cw_db = group_fep21.enroll_in_course(
        db_factory,
        lecture_time="Tue 14:00",
        lecture_room="202",
        lecture_teacher=lecturer_db,
        practical_time="Tue 14:00",  # спеціально конфлікт
        practical_room="Lab B",
        practical_teacher=assistant_db,
        supervisor=assistant_db,
    )

    cw_math = group_fep22.enroll_in_course(
        math_factory,
        lecture_time="Thu 09:00",
        lecture_room="303",
        lecture_teacher=lecturer_math,
        practical_time="Fri 11:00",
        practical_room="Room 5",
        practical_teacher=assistant_math,
        supervisor=lecturer_math,
    )

    print(f"{group_fep21.name} coursework 1: {cw_prog.submission_type()} — {cw_prog.title}")
    print(f"{group_fep21.name} coursework 2: {cw_db.submission_type()} — {cw_db.title}")
    print(f"{group_fep22.name} coursework: {cw_math.submission_type()} — {cw_math.title}")

    print("\nSchedule for", group_fep21.name)
    for s in group_fep21.sessions:
        print(f"{s.time}: {s.course_name} {s.kind()} in {s.room} with {s.teacher.name}")

    conflicts = group_fep21.check_conflicts()
    print("\nConflicts for", group_fep21.name)
    for a, b in conflicts:
        print(f"Conflict at {a.time}: {a.course_name} {a.kind()} / {b.course_name} {b.kind()}")


if __name__ == "__main__":
    main()
