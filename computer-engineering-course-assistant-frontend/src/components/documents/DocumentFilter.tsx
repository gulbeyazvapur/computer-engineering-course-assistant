import type { Course } from "../../types/course";

interface DocumentFilterProps {
  courses: Course[];
  value?: number;
  onChange: (courseId?: number) => void;
}

export default function DocumentFilter({
  courses,
  value,
  onChange,
}: DocumentFilterProps) {
  return (
    <div>
      <label
        htmlFor="document-filter"
        className="mb-1.5 block text-sm font-semibold text-charcoal"
      >
        Derse göre filtrele
      </label>
      <select
        id="document-filter"
        value={value ?? ""}
        onChange={(event) =>
          onChange(event.target.value ? Number(event.target.value) : undefined)
        }
        className="w-full rounded-lg border border-warm-border bg-white px-3 py-2.5 text-sm text-charcoal outline-none focus:border-terracotta focus:ring-2 focus:ring-terracotta/10 sm:max-w-xs"
      >
        <option value="">Tümü</option>
        {courses.map((course) => (
          <option key={course.id} value={course.id}>
            {course.name}
          </option>
        ))}
      </select>
    </div>
  );
}
