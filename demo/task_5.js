function findDuplicates(arr) {
    let resultSort = {};
    let final = []
    for (let value of arr){
        if (resultSort[value]){
            resultSort[value] += 1;
        }else{
            resultSort[value] = 1
        }
    }
    for (let key in resultSort){
        if (resultSort[key] > 1){
        final.push(Number(key))
        }
    }
    return final;
    }


const numbers = [1, 2, 3, 4, 2, 5, 1];
console.log(findDuplicates(numbers)); // [1, 2]