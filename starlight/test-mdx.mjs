import { compile } from '@mdx-js/mdx';

const code1 = `<EssayResponse client:only="react" title={""} prompt={"Test"} modelAnswer={"Line 1\\nLine 2"} />`;
const code2 = `<EssayResponse client:only="react" title={""} prompt={"Test"} modelAnswer={\`Line 1\nLine 2\`} />`;

const code3 = `
<EssayResponse client:only="react" title={""} prompt={"Test"} modelAnswer={\`Моя найкраща подруга Олена — надзвичайно цікава особистість.
Другий рядок тексту.
\`} />
`;

async function run() {
    try {
        await compile(code1);
        console.log("code1 compiled");
    } catch (e) {
        console.log("code1 failed", e.message);
    }
    try {
        await compile(code2);
        console.log("code2 compiled");
    } catch (e) {
        console.log("code2 failed", e.message);
    }
    try {
        await compile(code3);
        console.log("code3 compiled");
    } catch (e) {
        console.log("code3 failed", e.message);
    }
}
run();