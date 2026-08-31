import type { Course } from "../../types/course";

interface CourseSelectorProps {
  courses: Course[];
  value: number | null;
  onChange: (courseId: number | null) => void;
  disabled?: boolean;
}

export default function CourseSelector({
  courses,
  value,
  onChange,
  disabled = false,
}: CourseSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor="course-selector"
        className="text-sm font-semibold text-charcoal"
      >
        Ders
      </label>
      <select
        id="course-selector"
        value={value ?? ""}
        onChange={(event) =>
          onChange(event.target.value ? Number(event.target.value) : null)
        }
        disabled={disabled}
        className="w-full rounded-lg border border-warm-border bg-white px-3 py-2.5 text-sm text-charcoal outline-none transition focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 disabled:bg-cream-soft"
      >
        <option value="">Ders seçin</option>
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.name}
          </option>
        ))}
      </select>
    </div>
  );
}
