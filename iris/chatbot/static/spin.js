const tasks = [
    "Go for a short walk",
    "Cook your favourite meal",
    "Declutter a small space",
    "5 Things you are grateful for",
    "Listen to your favourite music",
    "Note today's accomplishment",
    "Throw away expired stuff",
    "Do a D.I.Y activity"
  ];
  
  const colors = [
    "#FF5733", "#FFC300", "#DAF7A6", "#33FF57",
    "#33D4FF", "#8A33FF", "#FF33A8", "#FF8C33"
  ];
  
  const canvas = document.getElementById("wheel");
  const ctx = canvas.getContext("2d");
  const resultDiv = document.getElementById("result");
  const spinButton = document.getElementById("spin-button");
  
  const wheelSize = tasks.length;
  const segmentAngle = 360 / wheelSize; // Each segment's angle
  const radius = canvas.width / 2;
  
  let isSpinning = false;
  let currentRotation = 0; // Tracks the current rotation of the wheel
  
  function drawWheel() {
    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear canvas
    for (let i = 0; i < wheelSize; i++) {
      const startAngle = (i * segmentAngle * Math.PI) / 180;
      const endAngle = ((i + 1) * segmentAngle * Math.PI) / 180;
  
      // Draw the segment
      ctx.beginPath();
      ctx.moveTo(radius, radius);
      ctx.arc(radius, radius, radius, startAngle, endAngle);
      ctx.fillStyle = colors[i];
      ctx.fill();
      ctx.strokeStyle = "black";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.closePath();
  
      // Draw the text
      ctx.save();
      const angle = startAngle + (endAngle - startAngle) / 2;
      ctx.translate(
        radius + Math.cos(angle) * radius * 0.6,
        radius + Math.sin(angle) * radius * 0.6
      );
      ctx.rotate(angle);
  
      // Split text into multiple lines if necessary
      const task = tasks[i];
      const words = task.split(" ");
      const line1 = words.slice(0, Math.ceil(words.length / 2)).join(" ");
      const line2 = words.slice(Math.ceil(words.length / 2)).join(" ");
  
      ctx.textAlign = "center";
      ctx.fillStyle = "white";
      ctx.font = "bold 12px Arial";
      ctx.fillText(line1, 0, -10); // First line of text
      ctx.fillText(line2, 0, 10);  // Second line of text
      ctx.restore();
    }
  }
  
  function spin() {
    if (isSpinning) return; // Prevent multiple spins
    isSpinning = false;
  
    const randomDegree = Math.floor(3600 + Math.random() * 360); // Random spin (10-11 rotations)
    const finalRotation = (randomDegree + currentRotation) % 360; // Total rotation angle
    const winningIndex = Math.floor(
      (360 - finalRotation + segmentAngle / 2) / segmentAngle
    ) % wheelSize;
  
    // Apply smooth spin
    canvas.style.transition = "transform 6s cubic-bezier(0.17, 0.67, 0.83, 0.67)";
    canvas.style.transform = `rotate(${randomDegree + currentRotation}deg)`;
  
    setTimeout(() => {
      // Align the winning segment at the top
      const stopRotation = 360 - winningIndex * segmentAngle;
      canvas.style.transition = "none";
      canvas.style.transform = `rotate(${stopRotation}deg)`;
  
      // Display the result
      resultDiv.textContent = `Task: ${tasks[winningIndex]}`;
      currentRotation = stopRotation % 360; // Update current rotation
      isSpinning = false;
    }, 3000); // Wait for spin animation to complete
  }
  
  // Draw the initial wheel
  drawWheel();
  spinButton.addEventListener("click", spin);

  function logout() {
    window.location.href = "login.html";
  }
