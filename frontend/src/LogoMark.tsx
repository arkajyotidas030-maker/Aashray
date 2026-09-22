export function LogoMark({
  className = "h-11 w-11",
  crop = true,
}: {
  className?: string;
  crop?: boolean;
}) {
  return (
    <img
      src="/aashray-logo.png"
      alt="AASHRAY"
      className={`${crop ? "object-cover object-[center_22%]" : "object-contain"} ${className}`}
    />
  );
}
