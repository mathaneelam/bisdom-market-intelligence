try {
  const { machineIdSync } = await import("node-machine-id");
  console.log("SUCCESS IMPORT! Machine ID:", machineIdSync());
} catch (e) {
  console.error("FAIL IMPORT:", e);
}
