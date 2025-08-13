let cost = Number(prompt("enter cost: "));
let n = Number(prompt("enter cant"));

// let number = 1
// while (number <= n) {
//     console.log(`Cant: ${number} cost: ${number*cost}`)
//      number += 1
// }
for (let number = 1; number <= n; number++) {
    console.log(`Cant: ${number} cost: ${number*cost}`)
}