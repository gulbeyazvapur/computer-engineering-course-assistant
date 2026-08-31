import Alert from "../components/common/Alert";
import Loader from "../components/common/Loader";
import CourseCard from "../components/courses/CourseCard";
import CreateCourseForm from "../components/courses/CreateCourseForm";
import { useCourses } from "../hooks/useCourses";

export default function CoursesPage() {
  const { courses, isLoading, error, refreshCourses } = useCourses();

  return (
    <section className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-charcoal">Dersler</h2>
        <p className="mt-1 text-sm text-warm-gray">
          Bilgi tabanındaki dersleri yönetin.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div>
          {error && <Alert kind="error">{error}</Alert>}

          {isLoading ? (
            <Loader label="Dersler yükleniyor..." />
          ) : courses.length === 0 ? (
            <div className="rounded-lg border border-dashed border-warm-border bg-white p-10 text-center text-sm text-warm-gray">
              Henüz ders eklenmedi.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {courses.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  onChanged={refreshCourses}
                />
              ))}
            </div>
          )}
        </div>

        <CreateCourseForm onCreated={refreshCourses} />
      </div>
    </section>
  );
}
