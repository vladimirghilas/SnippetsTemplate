const data = { a: 1, b: 2, c: 3 };

function sumObjectValues(obj) {
    let total = 0;
    for (let value of Object.values(obj)){
        total += value;
  }
    return total
}

console.log(sumObjectValues(data));