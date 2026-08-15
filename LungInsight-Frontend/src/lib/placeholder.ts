// Placeholder chest X-ray used for mock predictions and as a fallback
// while a real image URL is loading -- swapped for the real uploaded
// image URL (from getPredictionImageUrl) once the backend has one.
export const PLACEHOLDER_IMAGE =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="440" viewBox="0 0 400 440"><rect width="400" height="440" fill="#0d1524"/><ellipse cx="150" cy="220" rx="90" ry="170" fill="none" stroke="#3d4a63" stroke-width="3"/><ellipse cx="260" cy="220" rx="90" ry="170" fill="none" stroke="#3d4a63" stroke-width="3"/><rect x="195" y="60" width="20" height="320" fill="#3d4a63" opacity="0.6"/></svg>`
  );
