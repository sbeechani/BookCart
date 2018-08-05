var cartArray = new Array(10)

function addcart(x)
{
    i = x.slice(1);
    cartArray[i] = cartArray[i]+1;
    console.log(cartArray);
};