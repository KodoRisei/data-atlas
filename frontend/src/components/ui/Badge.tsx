import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "blue" | "green" | "red" | "amber" | "slate";
  className?: string;
}

export default function Badge({
  children,
  variant = "slate",
  className,
}: BadgeProps) {
  return (
    <span className={cn(`badge-${variant}`, className)}>{children}</span>
  );
}
