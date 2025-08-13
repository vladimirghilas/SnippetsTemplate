function findLongestWord(words) {
    let longhestWord = words[0]
    for (let word of words) {
        if (word.length > longhestWord.length) {
            longhestWord = word
        }
    }
    return longhestWord
}

const words = ["apple", "banana", "kiwi", "grapefruit"];
console.log(findLongestWord(words));